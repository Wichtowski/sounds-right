import { ApiStatusBadge } from "@components/ApiStatusBadge";
import { AppShell } from "@components/AppShell";
import { HomeIntro } from "@components/pages/home/HomeIntro";

export default function HomePage() {
  return (
    <AppShell>
      <section className="grid gap-8 py-10 lg:grid-cols-[1.3fr_0.7fr]">
        <HomeIntro artistsHref="/artists" registerHref="/register" />
        <ApiStatusBadge />
      </section>
    </AppShell>
  );
}
