export function Header() {
  return (
    <header className="flex items-center gap-3 border-b border-neutral-800 px-4 py-3">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold">
        TM
      </div>
      <div>
        <h1 className="text-sm font-semibold text-neutral-100">TaskMind AI</h1>
        <p className="text-xs text-neutral-500">Agent with real tool use — it doesn't just answer, it acts</p>
      </div>
    </header>
  );
}
