"use client";
import { useState, useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

type Message = { role: "user" | "assistant"; text: string };

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Bonjour ! Je suis votre assistant juridique. Posez-moi vos questions sur cette analyse de conformité." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: msg }]);
    setLoading(true);

    try {
      const res = await fetch(`/api/chat/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      const answer = res.ok ? data.answer : (data.detail ?? "Erreur serveur");
      setMessages((prev) => [...prev, { role: "assistant", text: answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", text: "Erreur de connexion." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[80vh]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-blue-800">Assistant juridique</h1>
        <Link href={`/analyses/${id}`} className="text-sm text-gray-400 hover:text-gray-600">
          ← Retour aux résultats
        </Link>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-white rounded-xl shadow p-4 space-y-4 mb-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap
                ${m.role === "user"
                  ? "bg-blue-700 text-white rounded-br-none"
                  : "bg-gray-100 text-gray-800 rounded-bl-none"}`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-500 px-4 py-3 rounded-2xl rounded-bl-none text-sm animate-pulse">
              ⟳ Réflexion en cours…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Posez votre question juridique…"
          className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="bg-blue-700 hover:bg-blue-800 disabled:bg-gray-300 text-white px-6 py-3 rounded-xl text-sm font-medium transition"
        >
          Envoyer
        </button>
      </div>
    </div>
  );
}
