import { type ReactNode, useState } from "react";
import "./App.css";

type SourceDocument = {
  title: string;
  summary: string;
  quote?: string | null;
  source?: string | null;
  source_type?: string | null;
  score: number;
};

type ChatResponse = {
  session_id: string;
  answer: string;
  sources: SourceDocument[];
  mode: string;
  market_snapshot?: StockSnapshot | null;
  decision_state?: string | null;
  evidence_score?: number | null;
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
  current_assets?: number | null;
  current_liabilities?: number | null;
  cash_and_equivalents?: number | null;
  total_debt?: number | null;
  operating_cash_flow?: number | null;
  capital_expenditures?: number | null;
  free_cash_flow?: number | null;
  current_ratio?: number | null;
  debt_to_equity?: number | null;
  working_capital?: number | null;
  annual_history?: Array<Record<string, number | null>>;
  earnings_years?: number | null;
  positive_earnings_years?: number | null;
  latest_annual_revenue?: number | null;
  oldest_annual_revenue?: number | null;
  latest_annual_eps?: number | null;
  oldest_annual_eps?: number | null;
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
  marketSnapshot?: StockSnapshot | null;
  decisionState?: string | null;
  evidenceScore?: number | null;
};

const starterQuestions = [
  "Does AAPL offer a margin of safety at the current price?",
  "Should MSFT be examined as a growth stock or a value investment?",
  "What does margin of safety mean when the market is enthusiastic?",
  "When should a defensive investor pass on an opportunity?",
];

const principles = [
  { label: "Margin of Safety", value: "Demand a gap between price and conservative value." },
  { label: "Intrinsic Value", value: "Estimate with evidence, not enthusiasm." },
  { label: "Temperament", value: "Emotional discipline is part of the investment method." },
  { label: "Evidence First", value: "Separate facts, assumptions, and judgment." },
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

function renderInline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={`${part}-${index}`}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

function renderMarkdown(content: string) {
  return (
    <div className="markdown-body">
      {content.split(/\n{2,}/).map((block, blockIndex) => {
        const lines = block.split("\n").filter(Boolean);
        if (lines.length > 0 && lines.every((line) => line.trim().startsWith("- "))) {
          return (
            <ul key={`${block}-${blockIndex}`}>
              {lines.map((line, lineIndex) => (
                <li key={`${line}-${lineIndex}`}>{renderInline(line.replace(/^\s*-\s*/, ""))}</li>
              ))}
            </ul>
          );
        }
        return (
          <p key={`${block}-${blockIndex}`}>
            {lines.map((line, lineIndex) => (
              <span key={`${line}-${lineIndex}`}>
                {renderInline(line)}
                {lineIndex < lines.length - 1 ? <br /> : null}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Give me a ticker, an investment thesis, or a valuation question. I will weigh the evidence, the price, the balance sheet, and the margin of safety.",
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

      if (!response.ok) throw new Error("Could not reach the research backend.");
      const data = (await response.json()) as ChatResponse;
      setSessionId(data.session_id);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
          mode: data.mode,
          marketSnapshot: data.market_snapshot,
          decisionState: data.decision_state,
          evidenceScore: data.evidence_score,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: error instanceof Error ? error.message : "The question could not be processed.",
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
      if (!response.ok) throw new Error("The market-data request is invalid.");
      setStock((await response.json()) as StockSnapshot);
    } catch (error) {
      setStock(null);
      setStockError(error instanceof Error ? error.message : "Market-data error.");
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
                    <span>{message.role === "user" ? "You" : "Graham"}</span>
                    {message.mode ? <small>{message.mode}</small> : null}
                  </div>
                  {renderMarkdown(message.content)}
                  {message.decisionState ? (
                    <div className="decision-strip">
                      <span>{message.decisionState.replace(/_/g, " ")}</span>
                      {message.evidenceScore !== null && message.evidenceScore !== undefined ? (
                        <strong>{message.evidenceScore}/100 evidence</strong>
                      ) : null}
                    </div>
                  ) : null}
                  {message.marketSnapshot ? (
                    <div className="market-evidence">
                      <strong>{message.marketSnapshot.symbol} evidence used</strong>
                      <span>
                        {message.marketSnapshot.source || "Market data"} · {message.marketSnapshot.status || "unknown"}
                        {message.marketSnapshot.as_of ? ` · ${message.marketSnapshot.as_of}` : ""}
                      </span>
                    </div>
                  ) : null}
                  {message.sources && message.sources.length > 0 ? (
                    <div className="sources">
                      {message.sources.map((source) => (
                        <div className="source" key={source.title}>
                          <strong>{source.title}</strong>
                          {source.source ? <em>{source.source}</em> : null}
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
                  <p>Weighing price, evidence, balance sheet strength, and margin of safety...</p>
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
                placeholder="Ask a question, for example: Does MSFT offer a margin of safety at the current price?"
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
                <div>
                  <dt>Current Ratio</dt>
                  <dd>{formatNumber(stock?.current_ratio)}</dd>
                </div>
                <div>
                  <dt>Debt / Equity</dt>
                  <dd>{formatNumber(stock?.debt_to_equity)}</dd>
                </div>
                <div>
                  <dt>Working Capital</dt>
                  <dd>{formatMarketCap(stock?.working_capital)}</dd>
                </div>
                <div>
                  <dt>Free Cash Flow</dt>
                  <dd>{formatMarketCap(stock?.free_cash_flow)}</dd>
                </div>
                <div>
                  <dt>Cash</dt>
                  <dd>{formatMarketCap(stock?.cash_and_equivalents)}</dd>
                </div>
                <div>
                  <dt>Total Debt</dt>
                  <dd>{formatMarketCap(stock?.total_debt)}</dd>
                </div>
                <div>
                  <dt>Earnings Record</dt>
                  <dd>
                    {stock?.positive_earnings_years ?? "N/A"} / {stock?.earnings_years ?? "N/A"} yrs
                  </dd>
                </div>
                <div>
                  <dt>Annual EPS</dt>
                  <dd>
                    {formatNumber(stock?.oldest_annual_eps)} → {formatNumber(stock?.latest_annual_eps)}
                  </dd>
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
