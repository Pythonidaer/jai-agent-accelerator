import { motion, AnimatePresence } from "framer-motion";
import {
  Loader2,
  CheckCircle2,
  Send,
  FileText,
  Target,
  DollarSign,
  AlertTriangle,
  Rocket,
  Users,
  Crosshair,
  BarChart3,
  ClipboardList,
  Sparkles,
  User,
  Command,
  MessageSquare,
  Swords,
  TrendingUp,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

// =============================================================================
// CONFIGURATION
// =============================================================================

// Use relative URLs in production (works with Netlify redirects)
// Only use localhost in development
const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.DEV ? "http://localhost:8123" : "/api");

// Tool display config with icons
const TOOL_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  analyze_product: { label: "Analyzing product", icon: "FileText", color: "blue" },
  extract_value_props: { label: "Extracting value props", icon: "Target", color: "purple" },
  identify_icp: { label: "Defining ICP", icon: "Users", color: "indigo" },
  search_competitors: { label: "Researching competitors", icon: "Crosshair", color: "red" },
  analyze_pricing: { label: "Analyzing pricing", icon: "DollarSign", color: "green" },
  fetch_url: { label: "Fetching data", icon: "BarChart3", color: "gray" },
  analyze_reviews: { label: "Mining reviews", icon: "MessageSquare", color: "yellow" },
  create_positioning_statement: { label: "Creating positioning", icon: "Target", color: "emerald" },
  create_messaging_matrix: { label: "Building messaging matrix", icon: "ClipboardList", color: "purple" },
  create_battlecard: { label: "Creating battlecard", icon: "Swords", color: "orange" },
  create_launch_plan: { label: "Building launch plan", icon: "Rocket", color: "blue" },
  create_checklist: { label: "Generating checklist", icon: "ClipboardList", color: "gray" },
  assess_market_risks: { label: "Assessing market risks", icon: "AlertTriangle", color: "red" },
  validate_positioning: { label: "Validating positioning", icon: "CheckCircle2", color: "green" },
  identify_gaps: { label: "Identifying gaps", icon: "TrendingUp", color: "yellow" },
};

// Quick actions - PMM workflows
const QUICK_ACTIONS = [
  {
    label: "Competitive Analysis",
    prompt: "Help me analyze the competitive landscape for my product.",
    icon: Crosshair,
    color: "red",
  },
  {
    label: "Positioning Statement",
    prompt: "Help me create a positioning statement for my product.",
    icon: Target,
    color: "emerald",
  },
  {
    label: "Messaging Matrix",
    prompt: "Help me build a messaging matrix with value props and proof points.",
    icon: MessageSquare,
    color: "purple",
  },
  {
    label: "Launch Plan",
    prompt: "Help me create a go-to-market launch plan.",
    icon: Rocket,
    color: "blue",
  },
  {
    label: "Battlecard",
    prompt: "Help me create a competitive battlecard.",
    icon: Swords,
    color: "orange",
  },
  {
    label: "ICP Definition",
    prompt: "Help me define my Ideal Customer Profile (ICP).",
    icon: Users,
    color: "indigo",
  },
  {
    label: "Pricing Analysis",
    prompt: "Analyze pricing strategies in my competitive landscape.",
    icon: DollarSign,
    color: "green",
  },
  {
    label: "Risk Assessment",
    prompt: "Run a market risk assessment on my positioning strategy.",
    icon: AlertTriangle,
    color: "yellow",
  },
];

// =============================================================================
// TYPES
// =============================================================================

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  status: "pending" | "running" | "completed";
}

// =============================================================================
// COMPONENTS
// =============================================================================

const IconMap: Record<string, React.FC<{ className?: string }>> = {
  FileText,
  Target,
  DollarSign,
  AlertTriangle,
  Rocket,
  Users,
  Crosshair,
  BarChart3,
  ClipboardList,
  MessageSquare,
  Swords,
  TrendingUp,
  CheckCircle2,
};

function ToolCallDisplay({ toolCall }: { toolCall: ToolCall }) {
  const config = TOOL_CONFIG[toolCall.name] || {
    label: toolCall.name,
    icon: "FileText",
    color: "gray",
  };
  const Icon = IconMap[config.icon] || FileText;
  const isRunning = toolCall.status === "running";

  return (
    <motion.div
      initial={{ opacity: 0, y: -10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex items-center gap-3 text-sm bg-slate-800/80 backdrop-blur rounded-lg px-4 py-2.5 border border-slate-700/50`}
    >
      {isRunning ? (
        <Loader2 className={`w-4 h-4 animate-spin text-${config.color}-400`} />
      ) : (
        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
      )}
      <Icon className={`w-4 h-4 text-${config.color}-400`} />
      <span className="font-medium text-slate-200">{config.label}</span>
    </motion.div>
  );
}

function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-violet-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
      )}

      <div
        className={`max-w-[80%] rounded-2xl p-5 ${
          isUser
            ? "bg-slate-700 text-white"
            : "bg-slate-800/80 backdrop-blur border border-slate-700/50"
        }`}
      >
        {/* Tool calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mb-4 space-y-2">
            <AnimatePresence>
              {message.toolCalls.map((tc) => (
                <ToolCallDisplay key={tc.id} toolCall={tc} />
              ))}
            </AnimatePresence>
          </div>
        )}

        {/* Content */}
        <div className={isUser ? "" : "prose prose-invert prose-sm max-w-none prose-headings:text-slate-100 prose-p:text-slate-300 prose-li:text-slate-300 prose-strong:text-slate-100 prose-code:text-violet-300 prose-code:bg-slate-700/50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded"}>
          {isUser ? (
            <p className="text-slate-100">{message.content}</p>
          ) : (
            <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
          )}
        </div>
      </div>

      {isUser && (
        <div className="w-10 h-10 rounded-xl bg-slate-700 flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-slate-300" />
        </div>
      )}
    </motion.div>
  );
}

function QuickActionButton({
  action,
  onSelect,
  disabled,
}: {
  action: typeof QUICK_ACTIONS[0];
  onSelect: () => void;
  disabled: boolean;
}) {
  const Icon = action.icon;

  return (
    <button
      onClick={onSelect}
      disabled={disabled}
      className={`flex items-center gap-3 px-4 py-3 bg-slate-800/60 border border-slate-700/50 rounded-xl hover:bg-slate-700/60 hover:border-slate-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed group`}
    >
      <div className={`p-2 rounded-lg bg-${action.color}-500/10 group-hover:bg-${action.color}-500/20 transition-colors`}>
        <Icon className={`w-4 h-4 text-${action.color}-400`} />
      </div>
      <span className="text-sm font-medium text-slate-200">{action.label}</span>
    </button>
  );
}

function WelcomeScreen({ onQuickAction }: { onQuickAction: (prompt: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mb-8 shadow-xl shadow-violet-500/30"
      >
        <Sparkles className="w-10 h-10 text-white" />
      </motion.div>

      <motion.h1
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="text-3xl font-bold text-slate-100 mb-3"
      >
        PMM Deep Agent
      </motion.h1>

      <motion.p
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-slate-400 mb-2 max-w-md"
      >
        Your product marketing intelligence assistant.
      </motion.p>

      <motion.p
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-slate-500 mb-10 text-sm"
      >
        Turn market chaos into messaging clarity. Position with confidence.
      </motion.p>

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-3xl"
      >
        {QUICK_ACTIONS.map((action) => (
          <QuickActionButton
            key={action.label}
            action={action}
            onSelect={() => onQuickAction(action.prompt)}
            disabled={false}
          />
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="mt-8 flex items-center gap-2 text-slate-500 text-xs"
      >
        <Command className="w-3 h-3" />
        <span>Type anything or click a quick action to start</span>
      </motion.div>
    </div>
  );
}

// =============================================================================
// MAIN APP
// =============================================================================

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setError(null);
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: content.trim(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInput("");
      setIsLoading(true);

      // Create placeholder assistant message
      const assistantMessageId = crypto.randomUUID();
      let assistantMessage: Message = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        toolCalls: [],
      };
      setMessages((prev) => [...prev, assistantMessage]);

      try {
        const response = await fetch(`${API_URL}/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: content.trim(),
            session_id: sessionId,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("No response body");
        }

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.type === "text") {
                  assistantMessage = {
                    ...assistantMessage,
                    content: assistantMessage.content + data.content,
                  };
                  setMessages((prev) => [
                    ...prev.slice(0, -1),
                    assistantMessage,
                  ]);
                } else if (data.type === "tool_call") {
                  const toolCall: ToolCall = {
                    id: crypto.randomUUID(),
                    name: data.name,
                    args: data.args,
                    status: "running",
                  };
                  assistantMessage = {
                    ...assistantMessage,
                    toolCalls: [...(assistantMessage.toolCalls || []), toolCall],
                  };
                  setMessages((prev) => [
                    ...prev.slice(0, -1),
                    assistantMessage,
                  ]);
                } else if (data.type === "done") {
                  if (data.session_id) {
                    setSessionId(data.session_id);
                  }
                  // Mark all tool calls as completed
                  if (assistantMessage.toolCalls?.length) {
                    assistantMessage = {
                      ...assistantMessage,
                      toolCalls: assistantMessage.toolCalls.map((tc) => ({
                        ...tc,
                        status: "completed" as const,
                      })),
                    };
                    setMessages((prev) => [
                      ...prev.slice(0, -1),
                      assistantMessage,
                    ]);
                  }
                }
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }
        }
      } catch (err) {
        console.error("Stream error:", err);
        setError(err instanceof Error ? err.message : "An error occurred");
        // Remove the empty assistant message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading]
  );

  const handleSubmit = () => {
    sendMessage(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900">
      {/* Header */}
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-100">PMM Deep Agent</h1>
            <p className="text-xs text-slate-500">Product marketing intelligence</p>
          </div>
        </div>
      </header>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeScreen onQuickAction={sendMessage} />
        ) : (
          <div className="max-w-4xl mx-auto p-6 space-y-6">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-900/50 border-t border-red-800 p-3 text-center text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-slate-800 p-4 bg-slate-900/80 backdrop-blur">
        <div className="max-w-4xl mx-auto">
          {/* Quick actions when in conversation */}
          {messages.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {QUICK_ACTIONS.slice(0, 4).map((action) => (
                <button
                  key={action.label}
                  onClick={() => sendMessage(action.prompt)}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
                >
                  <action.icon className="w-3 h-3 text-slate-400" />
                  <span className="text-slate-300">{action.label}</span>
                </button>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your product or ask a PMM question..."
              disabled={isLoading}
              className="flex-1 resize-none rounded-xl border border-slate-700 bg-slate-800 p-4 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              rows={1}
              style={{ minHeight: "56px", maxHeight: "200px" }}
            />
            <button
              onClick={handleSubmit}
              disabled={isLoading || !input.trim()}
              className="px-5 py-2 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-xl hover:from-violet-600 hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-violet-500/20"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
