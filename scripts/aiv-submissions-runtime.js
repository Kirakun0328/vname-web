(function () {
  'use strict';
  const payload = /* PAYLOAD */;
  const layerNames = ['VTUBER_DATA', 'VTUBER_EXTRA', 'VTUBER_PLATFORMS', 'VTUBER_PRIMARY'];
  const superseded = new Set(payload.superseded_ids);
  const byId = new Map();
  for (const name of layerNames) {
    window[name] = (window[name] || []).filter(row => !superseded.has(row.source_id));
    for (const row of window[name]) {
      if (!byId.has(row.source_id)) byId.set(row.source_id, []);
      byId.get(row.source_id).push(row);
    }
  }
  function accountKey(account) {
    try {
      const u = new URL(account.url);
      return account.platform + ':' + u.hostname.replace(/^www\./, '').replace(/^twitter\.com$/, 'x.com') + decodeURIComponent(u.pathname).toLowerCase().replace(/\/$/, '');
    } catch { return account.platform + ':' + account.id; }
  }
  for (const submitted of payload.records) {
    const targets = byId.get(submitted.source_id);
    if (!targets) {
      window.VTUBER_EXTRA.push(submitted);
      byId.set(submitted.source_id, [submitted]);
      continue;
    }
    const accounts = [...targets.flatMap(row => row.platform_accounts || []), ...submitted.platform_accounts];
    const mergedAccounts = [...new Map(accounts.map(account => [accountKey(account), account])).values()];
    const sources = [...new Set([...targets.flatMap(row => row.source_profiles || []), ...submitted.source_profiles])];
    for (const row of targets) Object.assign(row, submitted, {platform_accounts: mergedAccounts, source_profiles: sources});
  }
  // Expose review metadata for read-only validation, not as an additional data layer.
  window.VNameAIVSubmission = {date: '2026-09-11', count: payload.records.length};
})();
