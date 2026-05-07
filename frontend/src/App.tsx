import { useState } from "react";
import "./App.css";

type SourceDocument = {
  title: string;
  summary: string;
  quote?: string | null;
  score: number;
};

type ChatResponse = {
  session_id: string;
  answer: string;
  sources: SourceDocument[];
  mode: string;
};

type StockSnapshot = {
  symbol: string;
  company_name?: string | null;
  price?: number | null;
  pe?: number | null;
  roe?: number | null;
  eps?: number | null;
  market_cap?: number | null;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  volume?: number | null;
  as_of?: string | null;
  currency?: string | null;
  revenue?: number | null;
  net_income?: number | null;
  assets?: number | null;
  liabilities?: number | null;
  equity?: number | null;
  shares_outstanding?: number | null;
  fiscal_period?: string | null;
  source?: string;
  status?: "available" | "partial" | "unavailable";
  warning?: string | null;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: SourceDocument[];
  mode?: string;
};

const starterQuestions = [
  "Tôi nên đánh giá một cổ phiếu tăng trưởng như thế nào theo Graham?",
  "Biên an toàn có ý nghĩa gì khi thị trường đang hưng phấn?",
  "Khi nào một nhà đầu tư phòng thủ nên bỏ qua một cơ hội?",
];

const principles = [
  { label: "Margin of Safety", value: "Đòi hỏi khoảng cách giữa giá và giá trị." },
  { label: "Intrinsic Value", value: "Ước tính bằng dữ kiện, không bằng kỳ vọng." },
  { label: "Temperament", value: "Kỷ luật cảm xúc quan trọng như mô hình định giá." },
  { label: "Evidence First", value: "Tách dữ kiện, giả định và kết luận." },
];

function formatNumber(value?: number | null) {
  if (value === null || value === undefined) return "N/A";
  return Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function formatMarketCap(value?: number | null) {
  if (!value) return "N/A";
  if (value >= 1_000_000_000_000) return `${formatNumber(value / 1_000_000_000_000)}T`;
  if (value >= 1_000_000_000) return `${formatNumber(value / 1_000_000_000)}B`;
  if (value >= 1_000_000) return `${formatNumber(value / 1_000_000)}M`;
  return formatNumber(value);
}

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Tôi là InvestmentAI. Hãy đưa ticker, luận điểm đầu tư hoặc câu hỏi định giá; tôi sẽ phân tích theo kỷ luật Graham và chỉ rõ phần nào còn thiếu dữ kiện.",
      mode: "system",
    },
  ]);
  const [input, setInput] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [symbol, setSymbol] = useState("AAPL");
  const [stock, setStock] = useState<StockSnapshot | null>(null);
  const [stockError, setStockError] = useState("");
  const [loadingStock, setLoadingStock] = useState(false);

  async function ask(question = input) {
    const message = question.trim();
    if (!message || isAsking) return;

    setInput("");
    setIsAsking(true);
    setMessages((current) => [...current, { role: "user", content: message }]);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId }),
      });

      if (!response.ok) throw new Error("Không thể kết nối backend");
      const data = (await response.json()) as ChatResponse;
      setSessionId(data.session_id);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.answer, sources: data.sources, mode: data.mode },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: error instanceof Error ? error.message : "Có lỗi khi xử lý câu hỏi.",
          mode: "error",
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  }

  async function lookupStock() {
    const ticker = symbol.trim().toUpperCase();
    if (!ticker) return;
    setLoadingStock(true);
    setStockError("");

    try {
      const response = await fetch(`/api/stock/${encodeURIComponent(ticker)}`);
      if (!response.ok) throw new Error("Yêu cầu dữ liệu thị trường không hợp lệ");
      setStock((await response.json()) as StockSnapshot);
    } catch (error) {
      setStock(null);
      setStockError(error instanceof Error ? error.message : "Lỗi dữ liệu");
    } finally {
      setLoadingStock(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">InvestmentAI</p>
            <h1>Graham-style investment research</h1>
          </div>
          <div className="status-pill">
            <span className="status-dot" />
            Local research mode
          </div>
        </header>

        <div className="main-grid">
          <section className="chat-panel" aria-label="Investment chat">
            <div className="message-list">
              {messages.map((message, index) => (
                <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
                  <div className="message-meta">
                    <span>{message.role === "user" ? "You" : "InvestmentAI"}</span>
                    {message.mode ? <small>{message.mode}</small> : null}
                  </div>
                  <p>{message.content}</p>
                  {message.sources && message.sources.length > 0 ? (
                    <div className="sources">
                      {message.sources.map((source) => (
                        <div className="source" key={source.title}>
                          <strong>{source.title}</strong>
                          <span>{source.summary}</span>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))}
              {isAsking ? (
                <article className="message assistant">
                  <div className="message-meta">
                    <span>InvestmentAI</span>
                    <small>thinking</small>
                  </div>
                  <p>Đang kiểm tra nguyên tắc, dữ kiện và biên an toàn...</p>
                </article>
              ) : null}
            </div>

            <div className="starter-row">
              {starterQuestions.map((question) => (
                <button className="question-chip" onClick={() => void ask(question)} key={question}>
                  {question}
                </button>
              ))}
            </div>

            <form
              className="composer"
              onSubmit={(event) => {
                event.preventDefault();
                void ask();
              }}
            >
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Nhập câu hỏi: ví dụ MSFT có đủ biên an toàn ở mức giá hiện tại không?"
                rows={3}
              />
              <button type="submit" disabled={isAsking || !input.trim()}>
                Analyze
              </button>
            </form>
          </section>

          <aside className="research-rail" aria-label="Research tools">
            <section className="tool-panel">
              <h2>Market Snapshot</h2>
              <div className="ticker-form">
                <input value={symbol} onChange={(event) => setSymbol(event.target.value)} aria-label="Ticker" />
                <button onClick={() => void lookupStock()} disabled={loadingStock}>
                  Fetch
                </button>
              </div>
              {stock ? (
                <p className="data-source">
                  {stock.company_name ? `${stock.company_name} · ` : ""}
                  {stock.source || "Market data"}
                  {stock.as_of ? ` · Price ${stock.as_of}` : ""}
                  {stock.fiscal_period ? ` · SEC ${stock.fiscal_period}` : ""}
                </p>
              ) : null}
              {stockError ? <p className="error-text">{stockError}</p> : null}
              {stock?.warning ? <p className="warning-text">{stock.warning}</p> : null}
              <dl className="metrics">
                <div>
                  <dt>Price</dt>
                  <dd>
                    {stock?.currency ? `${stock.currency} ` : ""}
                    {formatNumber(stock?.price)}
                  </dd>
                </div>
                <div>
                  <dt>P/E</dt>
                  <dd>{formatNumber(stock?.pe)}</dd>
                </div>
                <div>
                  <dt>ROE</dt>
                  <dd>{stock?.roe ? `${formatNumber(stock.roe * 100)}%` : "N/A"}</dd>
                </div>
                <div>
                  <dt>EPS</dt>
                  <dd>{formatNumber(stock?.eps)}</dd>
                </div>
                <div>
                  <dt>Market Cap</dt>
                  <dd>{formatMarketCap(stock?.market_cap)}</dd>
                </div>
                <div>
                  <dt>Open</dt>
                  <dd>{formatNumber(stock?.open)}</dd>
                </div>
                <div>
                  <dt>High / Low</dt>
                  <dd>
                    {formatNumber(stock?.high)} / {formatNumber(stock?.low)}
                  </dd>
                </div>
                <div>
                  <dt>Volume</dt>
                  <dd>{formatNumber(stock?.volume)}</dd>
                </div>
                <div>
                  <dt>Revenue</dt>
                  <dd>{formatMarketCap(stock?.revenue)}</dd>
                </div>
                <div>
                  <dt>Net Income</dt>
                  <dd>{formatMarketCap(stock?.net_income)}</dd>
                </div>
                <div>
                  <dt>Assets</dt>
                  <dd>{formatMarketCap(stock?.assets)}</dd>
                </div>
                <div>
                  <dt>Equity</dt>
                  <dd>{formatMarketCap(stock?.equity)}</dd>
                </div>
              </dl>
            </section>

            <section className="tool-panel">
              <h2>Decision Discipline</h2>
              <div className="principle-list">
                {principles.map((principle) => (
                  <div className="principle" key={principle.label}>
                    <strong>{principle.label}</strong>
                    <span>{principle.value}</span>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </section>
    </main>
  );
}

export default App;
