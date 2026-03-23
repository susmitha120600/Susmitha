from typing import List, Dict, Any, Optional
import time
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    context_relevancy
)
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import EvaluationError
from app.models.schemas import RAGASMetrics, EvaluationResponse

logger = get_logger(__name__)


class Evaluator:
    
    def __init__(self):
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            context_relevancy
        ]
        logger.info("Evaluator initialized with RAGAS metrics")
    
    async def evaluate_rag_system(
        self,
        questions: List[str],
        answers: Optional[List[str]] = None,
        contexts: Optional[List[List[str]]] = None,
        ground_truths: Optional[List[str]] = None
    ) -> EvaluationResponse:
        try:
            start_time = time.time()
            
            logger.info(f"Evaluating RAG system with {len(questions)} questions")
            
            if not answers:
                raise EvaluationError("Answers are required for evaluation")
            
            if not contexts:
                raise EvaluationError("Contexts are required for evaluation")
            
            if len(questions) != len(answers) or len(questions) != len(contexts):
                raise EvaluationError("Questions, answers, and contexts must have the same length")
            
            data = {
                "question": questions,
                "answer": answers,
                "contexts": contexts
            }
            
            if ground_truths and len(ground_truths) == len(questions):
                data["ground_truth"] = ground_truths
            
            dataset = Dataset.from_dict(data)
            
            available_metrics = []
            if ground_truths:
                available_metrics = self.metrics
            else:
                available_metrics = [faithfulness, answer_relevancy, context_relevancy]
            
            logger.info(f"Running evaluation with metrics: {[m.name for m in available_metrics]}")
            
            result = evaluate(
                dataset=dataset,
                metrics=available_metrics
            )
            
            ragas_metrics = RAGASMetrics(
                faithfulness=result.get('faithfulness'),
                answer_relevancy=result.get('answer_relevancy'),
                context_precision=result.get('context_precision'),
                context_recall=result.get('context_recall'),
                context_relevancy=result.get('context_relevancy')
            )
            
            individual_scores = []
            for idx in range(len(questions)):
                score_dict = {
                    "question_index": idx,
                    "question": questions[idx]
                }
                
                for metric in available_metrics:
                    metric_name = metric.name
                    if metric_name in result:
                        score_dict[metric_name] = float(result[metric_name])
                
                individual_scores.append(score_dict)
            
            average_scores = {}
            for metric in available_metrics:
                metric_name = metric.name
                if metric_name in result:
                    average_scores[metric_name] = float(result[metric_name])
            
            evaluation_time = time.time() - start_time
            
            logger.info(f"Evaluation completed in {evaluation_time:.2f}s")
            logger.info(f"Average scores: {average_scores}")
            
            return EvaluationResponse(
                metrics=ragas_metrics,
                individual_scores=individual_scores,
                average_scores=average_scores,
                evaluation_time=evaluation_time
            )
            
        except Exception as e:
            logger.error(f"Evaluation error: {str(e)}")
            raise EvaluationError(f"Failed to evaluate RAG system: {str(e)}")
    
    async def evaluate_single_response(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        try:
            logger.info("Evaluating single response")
            
            questions = [question]
            answers = [answer]
            contexts_list = [contexts]
            ground_truths = [ground_truth] if ground_truth else None
            
            result = await self.evaluate_rag_system(
                questions=questions,
                answers=answers,
                contexts=contexts_list,
                ground_truths=ground_truths
            )
            
            return result.average_scores
            
        except Exception as e:
            logger.error(f"Single response evaluation error: {str(e)}")
            raise EvaluationError(f"Failed to evaluate response: {str(e)}")
    
    def calculate_custom_metrics(
        self,
        retrieved_chunks: List[str],
        relevant_chunks: List[str]
    ) -> Dict[str, float]:
        try:
            retrieved_set = set(retrieved_chunks)
            relevant_set = set(relevant_chunks)
            
            if not relevant_set:
                return {
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0
                }
            
            true_positives = len(retrieved_set.intersection(relevant_set))
            
            precision = true_positives / len(retrieved_set) if retrieved_set else 0.0
            recall = true_positives / len(relevant_set) if relevant_set else 0.0
            
            f1_score = (
                2 * (precision * recall) / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )
            
            return {
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "true_positives": true_positives,
                "false_positives": len(retrieved_set) - true_positives,
                "false_negatives": len(relevant_set) - true_positives
            }
            
        except Exception as e:
            logger.error(f"Custom metrics calculation error: {str(e)}")
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0
            }
