export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 p-6 dark:bg-zinc-950">
      <div className="w-full max-w-xl rounded border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h1 className="text-xl font-semibold">CFAI Frontend</h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Open the demo page to inspect persisted analysis payloads rendered together.
        </p>
        <a
          href="/demo/analysis"
          className="mt-4 inline-flex rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          Open Analysis Demo
        </a>
      </div>
    </main>
  );
}
