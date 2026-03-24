"use client";

import { NotificationPreference } from "@/lib/types";
import { useState } from "react";

type SettingsPanelProps = {
  preference: NotificationPreference;
};

export function SettingsPanel({ preference }: SettingsPanelProps) {
  const [keywords, setKeywords] = useState(preference.keywords.join(", "));
  const [emailEnabled, setEmailEnabled] = useState(preference.email_enabled);
  const [slackEnabled, setSlackEnabled] = useState(preference.slack_enabled);
  const [message, setMessage] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("설정 UI는 준비됐습니다. 토큰 인증을 연결하면 `/api/me/notifications`로 저장할 수 있습니다.");
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-5 rounded-[2rem] bg-white p-8 shadow-panel">
      <label className="text-sm font-semibold text-ink">
        Keywords
        <input
          value={keywords}
          onChange={(event) => setKeywords(event.target.value)}
          className="mt-2 w-full rounded-[1rem] border border-ink/10 px-4 py-3 text-sm font-normal"
        />
      </label>
      <label className="flex items-center gap-3 text-sm text-ink">
        <input type="checkbox" checked={emailEnabled} onChange={() => setEmailEnabled((value) => !value)} />
        Email alerts
      </label>
      <label className="flex items-center gap-3 text-sm text-ink">
        <input type="checkbox" checked={slackEnabled} onChange={() => setSlackEnabled((value) => !value)} />
        Slack webhook alerts
      </label>
      <button className="rounded-full bg-ember px-5 py-3 text-sm font-semibold text-white">Save preferences</button>
      <p className="text-sm text-ink/60">{message}</p>
    </form>
  );
}

