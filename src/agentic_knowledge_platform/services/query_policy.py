from __future__ import annotations

import re

from agentic_knowledge_platform.types import QuestionType


class QuestionPolicyService:
    confusing_pairs = (
        ("抢劫", "抢夺"),
        ("诈骗", "合同诈骗"),
        ("故意伤害", "故意杀人"),
        ("非法拘禁", "绑架"),
        ("危险驾驶", "交通肇事"),
        ("盗窃", "故意毁坏财物"),
    )

    def classify(self, query: str) -> QuestionType:
        question = query.strip()
        if self._is_refusal_case(question):
            return "should_refuse"
        if self._is_confusing_case(question):
            return "confusing"
        if self._is_definition_case(question):
            return "definition"
        if self._is_complex_reasoning_case(question):
            return "complex_reasoning"
        return "direct_answer"

    def top_k_for(self, question_type: QuestionType) -> int:
        mapping = {
            "direct_answer": 3,
            "definition": 4,
            "confusing": 6,
            "complex_reasoning": 5,
            "should_refuse": 3,
        }
        return mapping[question_type]

    def build_refusal_answer(self) -> str:
        return (
            "结论：根据当前检索到的证据，暂时无法直接作出确定性结论。\n"
            "依据：这类问题通常需要结合更具体的案件事实、行为方式、主观故意、结果后果和证据情况综合分析。\n"
            "说明：为避免误导，系统在证据不足或问题本身要求直接定性、量刑时会优先采取保守回答策略。"
        )

    def build_low_confidence_answer(self) -> str:
        return (
            "结论：当前证据不足，系统暂时无法给出高置信度回答。\n"
            "依据：已检索到的材料与问题之间的对应关系还不够充分，无法支撑进一步推断。\n"
            "说明：建议补充更完整的文档、案件事实或更明确的问题描述。"
        )

    def is_low_confidence(self, question: str, hits: list[object], question_type: QuestionType) -> bool:
        if not hits:
            return True

        top_contents = "".join(getattr(hit.chunk, "content", "") for hit in hits[:2]).strip()
        if len(top_contents) < 60:
            return True
        if question_type == "definition":
            return len(top_contents) < 80
        if question_type == "confusing":
            return len(top_contents) < 100
        if question_type == "complex_reasoning":
            return len(top_contents) < 120

        question_length = len(question.strip())
        if question_length > 26 and len(top_contents) < 90:
            return True
        return False

    def _is_refusal_case(self, question: str) -> bool:
        patterns = (
            r"能不能直接判断",
            r"能不能直接认定",
            r"一定会判几年",
            r"一定构成",
            r"一定就是",
            r"能不能断定",
            r"能不能直接下结论",
            r"能不能仅凭",
            r"只看.*能不能",
            r"是不是一定",
            r"一定会怎么判",
            r"能不能只根据.*判断",
        )
        return any(re.search(pattern, question) for pattern in patterns)

    def _is_confusing_case(self, question: str) -> bool:
        confusing_keywords = ("区别", "不同", "区分", "边界", "混淆", "相比", "比较")
        if any(keyword in question for keyword in confusing_keywords):
            return True
        return any(left in question and right in question for left, right in self.confusing_pairs)

    def _is_definition_case(self, question: str) -> bool:
        definition_keywords = (
            "是什么",
            "怎么理解",
            "叫什么",
            "定义",
            "属于什么",
            "在法律上叫什么",
            "一般指什么",
            "如何理解",
            "是什么意思",
        )
        return any(keyword in question for keyword in definition_keywords)

    def _is_complex_reasoning_case(self, question: str) -> bool:
        reasoning_keywords = (
            "一般怎么处理",
            "如何认定",
            "怎么评价",
            "是否属于",
            "如何定性",
            "如何处理",
            "是否构成",
        )
        multi_clause_keywords = ("如果", "同时", "并且", "造成", "超过", "结合")
        if any(keyword in question for keyword in reasoning_keywords):
            return True
        return sum(1 for keyword in multi_clause_keywords if keyword in question) >= 2
