import { createFileRoute } from "@tanstack/react-router";
import { LinkConsole } from "@/components/LinkConsole";
import { ThemeToggle } from "@/components/ThemeToggle";
import { CHANNELS, LANGUAGES } from "@/lib/itantra";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "iTantra — Offline Radio Voice Link" },
      {
        name: "description",
        content:
          "iTantra radio set: speech becomes a few bytes of text on one handset and is spoken again on the other, over low-bitrate radio channels. Fully offline, push-to-talk.",
      },
      { property: "og:title", content: "iTantra — Neural Transceiver for Low-Bitrate Radio" },
      {
        property: "og:description",
        content:
          "Tune a frequency, hold push-to-talk, and speak in English, Hindi, Bengali or Tamil. On-device STT sends text; on-device TTS speaks it at the far end.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const STEPS = [
  {
    step: "01",
    title: "Speak",
    body: "On-device STT runs behind a voice-activity gate and closes a sentence on a 350 ms pause.",
  },
  {
    step: "02",
    title: "Send",
    body: "The sentence goes out as a tiny text frame on the tuned frequency — around 90 bytes instead of 96 kB of audio.",
  },
  {
    step: "03",
    title: "Speak again",
    body: "The receiving set on the same frequency renders it with offline TTS. Alert traffic plays at full volume, uninterruptible.",
  },
];

function Index() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
      <div className="mb-6 flex justify-end">
        <ThemeToggle />
      </div>

      <header className="mb-8 text-center">
        <p className="label-etch">Offline · Open source · Low bitrate</p>
        <h1 className="mt-3 text-4xl font-bold sm:text-5xl">
          <span className="phosphor">iTantra</span>
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
          A radio set that carries voice over links too narrow for audio. Speech in, text on the
          air, speech out — English, Hindi, Bengali and Tamil, with no internet at all.
        </p>
      </header>

      <LinkConsole />

      <section className="mt-14" aria-labelledby="how">
        <h2 id="how" className="mb-4 text-center text-lg">
          How the link works
        </h2>
        <div className="grid gap-3 sm:grid-cols-3">
          {STEPS.map((s) => (
            <article key={s.step} className="panel-surface rounded-lg p-5">
              <p className="font-mono text-xs phosphor">{s.step}</p>
              <h3 className="mt-2 text-base font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{s.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-10 grid gap-3 sm:grid-cols-2" aria-labelledby="plan">
        <div className="panel-surface rounded-lg p-5">
          <h2 id="plan" className="mb-3 text-base">
            Link channel
          </h2>
          <ul className="space-y-1.5">
            {CHANNELS.map((c) => (
              <li key={c.id} className="flex justify-between font-mono text-sm">
                <span className="text-muted-foreground">{c.tag}</span>
                <span className="phosphor">{c.mhz.toFixed(3)} MHz</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel-surface rounded-lg p-5">
          <h2 className="mb-3 text-base">Language packs</h2>
          <ul className="space-y-1.5">
            {LANGUAGES.map((l) => (
              <li key={l.code} className="flex justify-between font-mono text-sm">
                <span className="text-muted-foreground">{l.name}</span>
                <span>{l.native}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">
            Quantised STT and TTS graphs, roughly 40 MB per language, running fully on the handset.
          </p>
        </div>
      </section>

      <footer className="mt-10 border-t border-etch pt-5 text-center text-xs text-muted-foreground">
        iTantra · offline speech transport for low-bitrate radio links.
      </footer>
    </main>
  );
}
