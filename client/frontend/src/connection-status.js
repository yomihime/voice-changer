// Explain an unavailable/incompatible backend without blocking offline UI development.
const status = document.createElement('div');
status.id = 'backend-status';
status.setAttribute('role', 'status');
status.hidden = true;
document.body.append(status);
async function check() {
  try {
    const response = await fetch('/api/configuration-manager/configuration', {
      signal: AbortSignal.timeout(4000), cache: 'no-store',
    });
    if (!response.ok) throw new Error(String(response.status));
    const data = await response.json();
    if (!data || typeof data !== 'object' || !('current_slot_index' in data)) throw new Error('Incompatible API');
    status.hidden = true;
  } catch {
    status.textContent = '未连接到兼容的 2.1.4 后端。请启动 2.x 服务并检查 --backend 地址；仓库旧版 /info 接口暂不兼容。';
    status.hidden = false;
  }
}
void check();
setInterval(check, 10000);
