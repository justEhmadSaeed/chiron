import { Send, Sparkles } from "lucide-react";
import { useState } from "react";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "assistant",
      content:
        "Hello! I'm your AI EXPERIMENT Assistant. Ask me anything about physics, chemistry, biology, astronomy, or any other science topic!",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: input,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMessage]);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: `Great question about "${input}"! This is a simulated response. In a real application, this would connect to an AI model to provide detailed scientific explanations, formulas, diagrams, and educational content tailored to your question.`,
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, aiMessage]);
    }, 1000);

    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-2xl rounded-2xl px-5 py-3 ${
                message.type === "user" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-100"
              }`}
            >
              {message.type === "assistant" && (
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles size={16} className="text-blue-400" />
                  <span className="text-xs text-slate-400">AI Assistant</span>
                </div>
              )}
              <p className="text-sm leading-relaxed">{message.content}</p>
              <p className="text-xs opacity-60 mt-2">{message.timestamp.toLocaleTimeString()}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="p-6 border-t border-slate-700">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask a science question..."
            className="flex-1 bg-slate-800 text-white placeholder-slate-500 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-6 py-3 flex items-center gap-2 transition-colors"
          >
            <Send size={18} />
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
