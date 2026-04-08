# { "Depends": "py-genlayer:test" }

import json
from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class OracleQuestion:
    id: u256
    question: str
    resolution_url: str
    outcome: str  # "UNRESOLVED" | "YES" | "NO" | "UNDETERMINED"
    confidence: u256  # 0-100
    reasoning: str
    resolved: bool


class BradburyOracle(gl.Contract):

    owner: Address
    question_count: u256
    questions: DynArray[OracleQuestion]
    total_resolved: u256
    yes_count: u256
    no_count: u256

    def __init__(self, owner_address: Address):
        self.owner = owner_address
        self.question_count = u256(0)
        self.total_resolved = u256(0)
        self.yes_count = u256(0)
        self.no_count = u256(0)

    @gl.public.view
    def get_question(self, question_id: u256) -> str:
        idx = int(question_id)
        if idx >= len(self.questions):
            return "Question not found"
        q = self.questions[idx]
        return (
            f"ID: {int(q.id)} | "
            f"Question: {q.question} | "
            f"Outcome: {q.outcome} | "
            f"Confidence: {int(q.confidence)}% | "
            f"Reasoning: {q.reasoning} | "
            f"Resolved: {q.resolved}"
        )

    @gl.public.view
    def get_question_count(self) -> u256:
        return self.question_count

    @gl.public.view
    def get_oracle_summary(self) -> str:
        return (
            f"Bradbury Intelligent Oracle\n"
            f"Total Questions: {int(self.question_count)}\n"
            f"Resolved: {int(self.total_resolved)}\n"
            f"YES outcomes: {int(self.yes_count)}\n"
            f"NO outcomes: {int(self.no_count)}\n"
            f"Pending: {int(self.question_count) - int(self.total_resolved)}"
        )

    @gl.public.view
    def get_outcome(self, question_id: u256) -> str:
        idx = int(question_id)
        if idx >= len(self.questions):
            return "Question not found"
        q = self.questions[idx]
        return q.outcome

    @gl.public.write
    def submit_question(self, question: str, resolution_url: str) -> None:
        pid = self.question_count
        oracle_q = OracleQuestion(
            id=pid,
            question=question,
            resolution_url=resolution_url,
            outcome="UNRESOLVED",
            confidence=u256(0),
            reasoning="Pending resolution",
            resolved=False,
        )
        self.questions.append(oracle_q)
        self.question_count = u256(int(pid) + 1)

    @gl.public.write
    def resolve(self, question_id: u256) -> str:
        idx = int(question_id)
        assert idx < len(self.questions), "Question not found"

        q = self.questions[idx]
        assert not q.resolved, "Already resolved"

        question_text = q.question
        resolution_url = q.resolution_url

        def leader_fn():
            response = gl.nondet.web.get(resolution_url)
            web_data = response.body.decode("utf-8")[:3000]

            prompt = f"""You are a decentralized prediction market oracle.
Your job is to determine the outcome of the following YES/NO question
based on the web page content provided.

Question: {question_text}

Web page content:
{web_data}

Analyze the content carefully and respond ONLY with a JSON object:
{{
  "outcome": "YES",
  "confidence": 90,
  "reasoning": "one sentence explanation based on the web data"
}}

Rules:
- outcome: must be exactly "YES", "NO", or "UNDETERMINED" if not enough info
- confidence: integer 0-100 reflecting how certain you are
- reasoning: one sentence citing specific evidence from the web page
- If the web page does not contain relevant information, use "UNDETERMINED"

Respond ONLY with the JSON, no extra text."""

            result = gl.nondet.exec_prompt(prompt)
            clean = result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

            outcome = data.get("outcome", "UNDETERMINED")
            confidence = int(data.get("confidence", 50))
            reasoning = data.get("reasoning", "")

            if outcome not in ("YES", "NO", "UNDETERMINED"):
                outcome = "UNDETERMINED"
            confidence = max(0, min(100, confidence))

            return json.dumps({
                "outcome": outcome,
                "confidence": confidence,
                "reasoning": reasoning
            }, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                validator_data = json.loads(validator_raw)

                if leader_data["outcome"] != validator_data["outcome"]:
                    return False

                return abs(leader_data["confidence"] - validator_data["confidence"]) <= 15

            except Exception:
                return False

        raw = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        data = json.loads(raw)

        outcome = data["outcome"]
        confidence = data["confidence"]
        reasoning = data["reasoning"]

        q.outcome = outcome
        q.confidence = u256(confidence)
        q.reasoning = reasoning
        q.resolved = True
        self.questions[idx] = q

        self.total_resolved = u256(int(self.total_resolved) + 1)
        if outcome == "YES":
            self.yes_count = u256(int(self.yes_count) + 1)
        elif outcome == "NO":
            self.no_count = u256(int(self.no_count) + 1)

        return f"Resolved: {outcome} ({confidence}% confidence) - {reasoning}"

    @gl.public.write
    def batch_submit(
        self,
        question1: str, url1: str,
        question2: str, url2: str,
        question3: str, url3: str
    ) -> None:
        for question, url in [(question1, url1), (question2, url2), (question3, url3)]:
            if question and url:
                pid = self.question_count
                oracle_q = OracleQuestion(
                    id=pid,
                    question=question,
                    resolution_url=url,
                    outcome="UNRESOLVED",
                    confidence=u256(0),
                    reasoning="Pending resolution",
                    resolved=False,
                )
                self.questions.append(oracle_q)
                self.question_count = u256(int(pid) + 1)

 
