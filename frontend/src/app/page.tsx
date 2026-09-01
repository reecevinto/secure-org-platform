export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 py-16">
      <section className="w-full max-w-2xl rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium text-zinc-500">
          Application Foundation
        </p>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900">
          Secure Organization Management Platform
        </h1>

        <p className="mt-4 text-base leading-7 text-zinc-600">
          The frontend application foundation is operational and ready for
          incremental feature development.
        </p>

        <dl className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-zinc-200 p-4">
            <dt className="text-sm font-medium text-zinc-500">Frontend</dt>
            <dd className="mt-1 text-sm text-zinc-900">
              Next.js + TypeScript
            </dd>
          </div>

          <div className="rounded-lg border border-zinc-200 p-4">
            <dt className="text-sm font-medium text-zinc-500">Backend</dt>
            <dd className="mt-1 text-sm text-zinc-900">
              FastAPI + Python
            </dd>
          </div>

          <div className="rounded-lg border border-zinc-200 p-4">
            <dt className="text-sm font-medium text-zinc-500">Environment</dt>
            <dd className="mt-1 text-sm text-zinc-900">Development</dd>
          </div>

          <div className="rounded-lg border border-zinc-200 p-4">
            <dt className="text-sm font-medium text-zinc-500">Status</dt>
            <dd className="mt-1 text-sm font-medium text-zinc-900">
              Foundation Ready
            </dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
