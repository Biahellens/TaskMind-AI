import { getToolMeta } from "../lib/toolMeta";
import type { ToolCallPart } from "../types";

export function ToolChip({ part }: { part: ToolCallPart }) {
  const meta = getToolMeta(part.name);
  const isRunning = part.status === "running";
  const isError = part.status === "error";

  return (
    <details className="group my-1 w-fit max-w-full rounded-lg border border-neutral-800 bg-neutral-900/60 open:bg-neutral-900">
      <summary
        className={[
          "flex cursor-pointer list-none items-center gap-2 px-3 py-1.5 text-sm select-none",
          isRunning ? "text-neutral-300" : isError ? "text-red-400" : "text-emerald-400",
        ].join(" ")}
      >
        <span className={isRunning ? "animate-pulse" : ""}>{meta.icon}</span>
        <span>{isRunning ? meta.running : isError ? "Failed" : meta.done}</span>
        {!isRunning && (
          <span className="ml-1 text-xs text-neutral-500 group-open:hidden">(view details)</span>
        )}
      </summary>
      <div className="border-t border-neutral-800 px-3 py-2 text-xs">
        <div className="mb-1 text-neutral-500">input</div>
        <pre className="mb-2 overflow-x-auto rounded bg-black/40 p-2 text-neutral-300">
          {JSON.stringify(part.input, null, 2)}
        </pre>
        {part.output !== undefined && (
          <>
            <div className="mb-1 text-neutral-500">output</div>
            <pre className="overflow-x-auto rounded bg-black/40 p-2 text-neutral-300">
              {JSON.stringify(part.output, null, 2)}
            </pre>
          </>
        )}
      </div>
    </details>
  );
}
