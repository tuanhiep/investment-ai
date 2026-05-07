from collections.abc import AsyncIterator
from uuid import uuid4
import asyncio

from openai import AsyncOpenAI

from backend.agents.prompt_graham import build_prompt
from backend.config.config import get_settings
from backend.schemas import ChatResponse, SourceDocument
from backend.services.knowledge import KnowledgeChunk, load_knowledge, retrieve


class InvestmentAdvisor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.knowledge = load_knowledge(self.settings.knowledge_file)
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def _context(self, matches: list[tuple[KnowledgeChunk, float]]) -> str:
        if not matches:
            return "No internal knowledge matched the question."
        return "\n\n".join(
            f"Title: {chunk.title}\nSummary: {chunk.summary}\nQuote: {chunk.quote or 'N/A'}"
            for chunk, _score in matches
        )

    def _sources(self, matches: list[tuple[KnowledgeChunk, float]]) -> list[SourceDocument]:
        return [
            SourceDocument(
                title=chunk.title,
                summary=chunk.summary,
                quote=chunk.quote,
                score=score,
            )
            for chunk, score in matches
        ]

    def _fallback_answer(self, question: str, matches: list[tuple[KnowledgeChunk, float]]) -> str:
        source = matches[0][0] if matches else None
        principle = source.title if source else "Margin of Safety"
        evidence = source.summary if source else "Chưa có đủ dữ liệu nội bộ để định giá doanh nghiệp cụ thể."

        return (
            f"**Nhận định trực tiếp:** Câu hỏi nên được xử lý bằng lăng kính `{principle}` trước khi nghĩ tới mua/bán.\n\n"
            f"**Lý luận kiểu Graham:** {evidence} Nhà đầu tư cần đòi hỏi biên an toàn, lợi nhuận bền vững, "
            "bảng cân đối lành mạnh và mức giá thấp hơn giá trị nội tại ước tính.\n\n"
            "**Rủi ro hoặc thiếu dữ kiện:** Tôi chưa có báo cáo tài chính, dòng tiền, nợ, lịch sử lợi nhuận và định giá "
            "so với doanh nghiệp cùng ngành trong câu hỏi này.\n\n"
            f"**Hành động tiếp theo:** Với câu hỏi `{question}`, hãy thu thập số liệu 5-10 năm, tính giá trị nội tại theo "
            "kịch bản thận trọng, rồi chỉ cân nhắc khi giá thị trường tạo đủ biên an toàn."
        )

    async def ask(self, message: str, session_id: str | None = None) -> ChatResponse:
        matches = retrieve(message, self.knowledge)
        sources = self._sources(matches)
        session = session_id or str(uuid4())

        if not self.client:
            return ChatResponse(
                session_id=session,
                answer=self._fallback_answer(message, matches),
                sources=sources,
                mode="local-fallback",
            )

        completion = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a rigorous investment research assistant."},
                {"role": "user", "content": build_prompt(message, self._context(matches))},
            ],
            temperature=0.25,
        )
        answer = completion.choices[0].message.content or ""
        return ChatResponse(session_id=session, answer=answer, sources=sources, mode="openai")

    async def stream(self, message: str) -> AsyncIterator[str]:
        matches = retrieve(message, self.knowledge)

        if not self.client:
            for token in self._fallback_answer(message, matches).split(" "):
                yield token + " "
                await asyncio.sleep(0.015)
            return

        stream = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a rigorous investment research assistant."},
                {"role": "user", "content": build_prompt(message, self._context(matches))},
            ],
            temperature=0.25,
            stream=True,
        )
        async for event in stream:
            token = event.choices[0].delta.content
            if token:
                yield token


advisor = InvestmentAdvisor()


async def answer_question(query: str) -> ChatResponse:
    return await advisor.ask(query)
