function $(id) {
  return document.getElementById(id);
}

function render(data) {
  $("meta").textContent = `${data.date} · 更新于 ${data.updated_at}（北京时间）`;
  $("greet-text").textContent = data.greeting.text;
  $("greet-lang").textContent = data.greeting.language;

  const list = $("news-list");
  list.innerHTML = "";
  if (!data.news || data.news.length === 0) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "暂未获取到新闻，请稍后刷新。";
    list.appendChild(li);
  } else {
    data.news.forEach((item) => {
      const li = document.createElement("li");
      li.className = "news-item";

      const rank = document.createElement("span");
      rank.className = "rank";
      rank.textContent = item.rank;

      const body = document.createElement("div");
      body.className = "news-body";

      const title = document.createElement("a");
      title.className = "news-title";
      title.href = item.link;
      title.target = "_blank";
      title.rel = "noopener";
      title.textContent = item.title;

      const meta = document.createElement("p");
      meta.className = "news-meta";
      const src = document.createElement("span");
      src.className = "src";
      src.textContent = item.source;
      meta.append(src, ` · ${item.published}`);

      body.append(title, meta);
      if (item.summary) {
        const summary = document.createElement("p");
        summary.className = "news-summary";
        summary.textContent = item.summary;
        body.appendChild(summary);
      }
      li.append(rank, body);
      list.appendChild(li);
    });
  }

  const grid = $("weather-grid");
  grid.innerHTML = "";
  data.weather.forEach((w) => {
    const card = document.createElement("div");
    card.className = "weather-card";
    card.innerHTML = `
      <h3>${w.city}</h3>
      <p class="w-icon">${w.icon}</p>
      <p class="w-now">${w.current != null ? w.current + "°C" : "—"}</p>
      <p class="w-cond">${w.condition}</p>
      <p class="w-range">最低 ${w.min != null ? w.min + "°" : "—"} · 最高 ${w.max != null ? w.max + "°" : "—"}</p>
    `;
    grid.appendChild(card);
  });
}

async function load() {
  try {
    const resp = await fetch("data.json?t=" + Date.now());
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    render(await resp.json());
  } catch (err) {
    $("meta").textContent = "数据加载失败，请确认已启动 server.py";
  }
}

load();
setInterval(load, 10 * 60 * 1000);
