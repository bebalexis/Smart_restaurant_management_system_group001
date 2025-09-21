async function jget(url){ const r = await fetch(url); return r.json(); }
async function jpost(url, data){ const r = await fetch(url,{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data||{})}); return {ok:r.ok, data: await r.json()}; }

function render(outEl, data){ outEl.textContent = JSON.stringify(data, null, 2); }

// MENU
const menuOut = document.getElementById('menuOut');
document.getElementById('refreshMenu').onclick = async ()=> render(menuOut, await jget('/api/menu'));
document.getElementById('addMenuForm').onsubmit = async (e)=>{
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  data.price = parseFloat(data.price);
  const res = await jpost('/api/menu', data);
  render(menuOut, res.data);
};

// TABLES
const tablesOut = document.getElementById('tablesOut');
document.getElementById('refreshTables').onclick = async ()=> render(tablesOut, await jget('/api/tables'));
document.getElementById('addTableForm').onsubmit = async (e)=>{
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  data.capacity = parseInt(data.capacity || '2', 10);
  const res = await jpost('/api/tables', data);
  render(tablesOut, res.data);
};

// RESERVATIONS
const reservationsOut = document.getElementById('reservationsOut');
document.getElementById('refreshReservations').onclick = async ()=> render(reservationsOut, await jget('/api/reservations'));
document.getElementById('addReservationForm').onsubmit = async (e)=>{
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  if (data.time) { data.time = new Date(data.time).toISOString(); }
  data.size = parseInt(data.size, 10);
  if (data.table_id) data.table_id = parseInt(data.table_id, 10);
  const res = await jpost('/api/reservations', data);
  render(reservationsOut, res.data);
};

// ORDERS
const ordersOut = document.getElementById('ordersOut');
document.getElementById('refreshOrders')?.addEventListener('click', async ()=> render(ordersOut, await jget('/api/orders')));
document.getElementById('addOrderForm').onsubmit = async (e)=>{
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const payload = {};
  if (data.table_id) payload.table_id = parseInt(data.table_id, 10);
  try { payload.items = JSON.parse(data.items || '[]'); } catch { payload.items = []; }
  const res = await jpost('/api/orders', payload);
  render(ordersOut, res.data);
};

// BILLING
const billingOut = document.getElementById('billingOut');
document.getElementById('payOrderForm').onsubmit = async (e)=>{
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const order_id = parseInt(data.order_id, 10);
  const payload = {};
  if (data.amount) payload.amount = parseFloat(data.amount);
  if (data.method) payload.method = data.method;
  const res = await jpost(`/api/orders/${order_id}/pay`, payload);
  render(billingOut, res.data);
};

// REPORTS
const reportsOut = document.getElementById('reportsOut');
document.getElementById('refreshReports').onclick = async ()=> render(reportsOut, await jget('/api/reports/sales'));

// LOGOUT
document.getElementById('logoutBtn').onclick = async ()=>{
  await jpost('/logout', {});
  location.href = '/login';
};

// LIVE EVENTS
const eventsOut = document.getElementById('eventsOut');
const socket = io({ transports: ['websocket'] });
socket.on('connect', ()=> { eventsOut.textContent += "Connected to live events\n"; });
socket.on('event', (payload)=>{
  eventsOut.textContent += JSON.stringify(payload) + "\n";
});


// ====== UPDATE/DELETE HANDLERS ======
async function jput(url, data){ const r = await fetch(url,{method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data||{})}); return {ok:r.ok, data: await r.json()}; }
async function jdel(url){ const r = await fetch(url,{method:'DELETE'}); return {ok:r.ok, data: await r.json()}; }

// Menu update/delete
document.getElementById('updateMenuForm').onsubmit = async (e)=>{
  e.preventDefault();
  const d = Object.fromEntries(new FormData(e.target).entries());
  const id = parseInt(d.id,10);
  const payload = {};
  ['name','category','available','price'].forEach(k=>{ if(d[k]) payload[k] = k==='price'?parseFloat(d[k]): (k==='available'? (d[k].toLowerCase()==='true'): d[k]); });
  const res = await jput(`/api/menu/${id}`, payload); render(menuOut, res.data);
};
document.getElementById('deleteMenuForm').onsubmit = async (e)=>{
  e.preventDefault();
  const id = parseInt(new FormData(e.target).get('id'),10);
  const res = await jdel(`/api/menu/${id}`); render(menuOut, res.data);
};

// Table update/delete
document.getElementById('updateTableForm').onsubmit = async (e)=>{
  e.preventDefault();
  const d = Object.fromEntries(new FormData(e.target).entries());
  const id = parseInt(d.id,10);
  const payload = {};
  if (d.label) payload.label = d.label;
  if (d.capacity) payload.capacity = parseInt(d.capacity,10);
  if (d.occupied) payload.occupied = (d.occupied.toLowerCase()==='true');
  const res = await jput(`/api/tables/${id}`, payload); render(tablesOut, res.data);
};
document.getElementById('deleteTableForm').onsubmit = async (e)=>{
  e.preventDefault();
  const id = parseInt(new FormData(e.target).get('id'),10);
  const res = await jdel(`/api/tables/${id}`); render(tablesOut, res.data);
};

// Reservation update/delete
document.getElementById('updateReservationForm').onsubmit = async (e)=>{
  e.preventDefault();
  const d = Object.fromEntries(new FormData(e.target).entries());
  const id = parseInt(d.id,10);
  const payload = {};
  if (d.name) payload.name = d.name;
  if (d.phone) payload.phone = d.phone;
  if (d.size) payload.size = parseInt(d.size,10);
  if (d.time) payload.time = new Date(d.time).toISOString();
  if (d.table_id) payload.table_id = parseInt(d.table_id,10);
  const res = await jput(`/api/reservations/${id}`, payload); render(reservationsOut, res.data);
};
document.getElementById('deleteReservationForm').onsubmit = async (e)=>{
  e.preventDefault();
  const id = parseInt(new FormData(e.target).get('id'),10);
  const res = await jdel(`/api/reservations/${id}`); render(reservationsOut, res.data);
};
