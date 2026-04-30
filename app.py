<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Control Pedidos · Princess Canarias</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* ── Reset & tokens ─────────────────────────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:   #0f2044;
  --navy2:  #1a3a6b;
  --gold:   #c9a84c;
  --gold2:  #e8c96a;
  --white:  #ffffff;
  --bg:     #f4f6fa;
  --bg2:    #eaecf2;
  --text:   #1c2b45;
  --muted:  #6b7a99;
  --border: #d5daea;
  --radius: 10px;
  --shadow: 0 2px 12px rgba(15,32,68,.10);
  --shadow-lg: 0 8px 32px rgba(15,32,68,.15);

  /* Estado colores */
  --s-pendiente-compras: #ffeeba;
  --s-pendiente-hotel:   #ffe0a0;
  --s-enviado:           #c8e6ff;
  --s-parcial:           #fff3cd;
  --s-entregado:         #c8f2d8;
  --s-anulado:           #ffd6d6;
}
html,body{height:100%;font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);font-size:14px}

/* ── Layout ─────────────────────────────────────────────────────────────── */
#app{display:flex;height:100vh;overflow:hidden}
#sidebar{
  width:220px;flex-shrink:0;background:var(--navy);
  display:flex;flex-direction:column;
  transition:width .25s ease
}
#main{flex:1;display:flex;flex-direction:column;overflow:hidden}
#topbar{
  height:56px;background:var(--white);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 24px;gap:16px;flex-shrink:0;
  box-shadow:0 1px 4px rgba(15,32,68,.06)
}
#content{flex:1;overflow-y:auto;padding:24px}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
.sb-logo{
  padding:20px 20px 16px;border-bottom:1px solid rgba(255,255,255,.08);
  display:flex;align-items:center;gap:10px
}
.sb-logo-icon{
  width:36px;height:36px;background:var(--gold);border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:16px;color:var(--navy);flex-shrink:0
}
.sb-logo-text{color:var(--white);font-size:13px;font-weight:600;line-height:1.3}
.sb-logo-sub{color:rgba(255,255,255,.45);font-size:11px}

.sb-section{padding:16px 12px 8px;color:rgba(255,255,255,.35);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}
.sb-item{
  display:flex;align-items:center;gap:10px;
  padding:9px 16px;margin:1px 8px;border-radius:7px;cursor:pointer;
  color:rgba(255,255,255,.65);font-size:13px;font-weight:500;
  transition:background .15s,color .15s
}
.sb-item:hover{background:rgba(255,255,255,.07);color:var(--white)}
.sb-item.active{background:rgba(201,168,76,.15);color:var(--gold2)}
.sb-item .icon{font-size:16px;width:20px;text-align:center}
.sb-badge{
  margin-left:auto;background:var(--gold);color:var(--navy);
  font-size:10px;font-weight:700;padding:1px 6px;border-radius:10px
}

.sb-bottom{margin-top:auto;padding:16px;border-top:1px solid rgba(255,255,255,.08)}
.sb-user{display:flex;align-items:center;gap:10px}
.sb-avatar{
  width:32px;height:32px;border-radius:50%;background:var(--navy2);
  display:flex;align-items:center;justify-content:center;
  font-size:12px;font-weight:700;color:var(--gold);flex-shrink:0
}
.sb-username{color:var(--white);font-size:12px;font-weight:500}
.sb-rol{color:rgba(255,255,255,.4);font-size:10px}

/* ── Topbar ─────────────────────────────────────────────────────────────── */
.tb-title{font-size:15px;font-weight:600;color:var(--text)}
.tb-actions{display:flex;gap:8px;margin-left:auto;align-items:center}

/* ── Botones ────────────────────────────────────────────────────────────── */
.btn{
  display:inline-flex;align-items:center;gap:6px;padding:7px 14px;
  border-radius:7px;border:none;cursor:pointer;font-family:inherit;
  font-size:13px;font-weight:500;transition:all .15s;white-space:nowrap
}
.btn-primary{background:var(--navy2);color:var(--white)}
.btn-primary:hover{background:var(--navy)}
.btn-gold{background:var(--gold);color:var(--navy);font-weight:600}
.btn-gold:hover{background:var(--gold2)}
.btn-ghost{background:transparent;color:var(--muted);border:1px solid var(--border)}
.btn-ghost:hover{background:var(--bg);color:var(--text)}
.btn-danger{background:#fee2e2;color:#b91c1c}
.btn-danger:hover{background:#fecaca}
.btn-sm{padding:5px 10px;font-size:12px}
.btn:disabled{opacity:.5;cursor:not-allowed}

/* ── Cards ──────────────────────────────────────────────────────────────── */
.card{background:var(--white);border-radius:var(--radius);border:1px solid var(--border);box-shadow:var(--shadow)}
.card-header{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px}
.card-title{font-size:14px;font-weight:600;color:var(--text)}
.card-body{padding:20px}

/* ── Stats cards ────────────────────────────────────────────────────────── */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px}
.stat-card{
  background:var(--white);border:1px solid var(--border);
  border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow)
}
.stat-num{font-size:28px;font-weight:700;color:var(--navy);line-height:1}
.stat-label{font-size:12px;color:var(--muted);margin-top:4px}
.stat-card.alert-card{border-color:#fbbf24;background:#fffbeb}
.stat-card.alert-card .stat-num{color:#b45309}

/* ── Tabla de pedidos ───────────────────────────────────────────────────── */
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
thead th{
  background:var(--bg);border-bottom:2px solid var(--border);
  padding:10px 12px;text-align:left;font-size:11px;font-weight:600;
  color:var(--muted);text-transform:uppercase;letter-spacing:.06em;
  white-space:nowrap
}
tbody tr{border-bottom:1px solid var(--border);cursor:pointer;transition:background .1s}
tbody tr:hover{background:var(--bg)}
tbody td{padding:10px 12px;font-size:13px;vertical-align:middle}
tbody tr:last-child{border-bottom:none}

/* Estado badge */
.badge{
  display:inline-flex;align-items:center;
  padding:3px 8px;border-radius:5px;font-size:11px;font-weight:600;
  white-space:nowrap
}
.badge-pendiente-compras{background:var(--s-pendiente-compras);color:#92400e}
.badge-pendiente-hotel  {background:var(--s-pendiente-hotel);color:#92400e}
.badge-enviado          {background:var(--s-enviado);color:#1e40af}
.badge-parcial          {background:var(--s-parcial);color:#78350f}
.badge-entregado        {background:var(--s-entregado);color:#065f46}
.badge-anulado          {background:var(--s-anulado);color:#991b1b}

/* Bool badge */
.bool-si{color:#059669;font-weight:600}
.bool-no{color:#d1d5db}

/* ── Filtros ────────────────────────────────────────────────────────────── */
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;align-items:center}
.filter-input,.filter-select{
  padding:7px 10px;border:1px solid var(--border);border-radius:7px;
  font-family:inherit;font-size:13px;background:var(--white);color:var(--text);
  outline:none;transition:border-color .15s
}
.filter-input:focus,.filter-select:focus{border-color:var(--navy2)}
.filter-input{width:200px}
.filter-select{min-width:160px}

/* ── Paginación ────────────────────────────────────────────────────────── */
.pagination{display:flex;align-items:center;gap:4px;justify-content:flex-end;margin-top:16px}
.page-btn{
  width:32px;height:32px;border:1px solid var(--border);border-radius:6px;
  background:var(--white);cursor:pointer;font-size:13px;
  display:flex;align-items:center;justify-content:center;
  transition:all .15s;color:var(--text)
}
.page-btn:hover{background:var(--bg);border-color:var(--navy2)}
.page-btn.active{background:var(--navy2);color:var(--white);border-color:var(--navy2)}
.page-btn:disabled{opacity:.4;cursor:not-allowed}
.page-info{font-size:12px;color:var(--muted);padding:0 8px}

/* ── Modal ──────────────────────────────────────────────────────────────── */
.modal-overlay{
  position:fixed;inset:0;background:rgba(15,32,68,.5);
  display:flex;align-items:center;justify-content:center;
  z-index:1000;opacity:0;pointer-events:none;transition:opacity .2s;
  backdrop-filter:blur(2px)
}
.modal-overlay.open{opacity:1;pointer-events:all}
.modal{
  background:var(--white);border-radius:14px;
  width:min(720px,95vw);max-height:90vh;overflow-y:auto;
  box-shadow:var(--shadow-lg);transform:translateY(20px);transition:transform .2s
}
.modal-overlay.open .modal{transform:translateY(0)}
.modal-header{
  padding:20px 24px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;background:var(--white);z-index:1
}
.modal-title{font-size:16px;font-weight:600}
.modal-body{padding:24px}
.modal-footer{
  padding:16px 24px;border-top:1px solid var(--border);
  display:flex;justify-content:flex-end;gap:8px;
  position:sticky;bottom:0;background:var(--white)
}
.close-btn{width:30px;height:30px;border-radius:50%;border:none;background:var(--bg);cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}

/* ── Formulario ─────────────────────────────────────────────────────────── */
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.form-grid.cols-3{grid-template-columns:1fr 1fr 1fr}
.form-group{display:flex;flex-direction:column;gap:5px}
.form-group.full{grid-column:1/-1}
.form-label{font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.form-control{
  padding:9px 12px;border:1px solid var(--border);border-radius:7px;
  font-family:inherit;font-size:13px;color:var(--text);
  outline:none;transition:border-color .15s;background:var(--white)
}
.form-control:focus{border-color:var(--navy2);box-shadow:0 0 0 3px rgba(26,58,107,.1)}
.form-section{
  grid-column:1/-1;padding-top:12px;border-top:1px solid var(--border);
  font-size:11px;font-weight:700;color:var(--navy2);
  text-transform:uppercase;letter-spacing:.08em;margin-top:4px
}
.checkbox-group{display:flex;flex-wrap:wrap;gap:12px}
.checkbox-item{display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px}
.checkbox-item input{width:15px;height:15px;accent-color:var(--navy2)}

/* ── Historial ──────────────────────────────────────────────────────────── */
.timeline{display:flex;flex-direction:column;gap:0}
.tl-item{display:flex;gap:12px;padding:10px 0;position:relative}
.tl-item:not(:last-child)::before{
  content:'';position:absolute;left:11px;top:30px;bottom:0;
  width:2px;background:var(--border)
}
.tl-dot{
  width:24px;height:24px;border-radius:50%;background:var(--navy2);
  flex-shrink:0;display:flex;align-items:center;justify-content:center;
  font-size:10px;color:var(--white);z-index:1
}
.tl-content{flex:1;padding-top:2px}
.tl-estado{font-weight:600;font-size:13px}
.tl-meta{font-size:11px;color:var(--muted);margin-top:2px}

/* ── Login ──────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&display=swap');
#login-screen{
  position:fixed;inset:0;
  background: radial-gradient(ellipse at 30% 40%, #1a2a1a 0%, #0a0e0a 40%, #050706 100%);
  display:flex;align-items:center;justify-content:center;z-index:9999;
  overflow:hidden;
}
#login-screen::before{
  content:'';position:absolute;inset:0;
  background: radial-gradient(ellipse at 70% 60%, rgba(180,150,60,0.08) 0%, transparent 60%);
  pointer-events:none;
}
#login-screen::after{
  content:'';position:absolute;inset:0;
  background-image: repeating-linear-gradient(0deg, transparent, transparent 60px, rgba(180,150,60,0.015) 60px, rgba(180,150,60,0.015) 61px),
                    repeating-linear-gradient(90deg, transparent, transparent 60px, rgba(180,150,60,0.015) 60px, rgba(180,150,60,0.015) 61px);
  pointer-events:none;
}
.login-box{
  background: linear-gradient(145deg, rgba(20,20,15,0.97) 0%, rgba(12,12,8,0.99) 100%);
  border-radius:4px;padding:52px 48px 44px;
  width:420px;
  border:1px solid rgba(180,150,60,0.25);
  box-shadow: 0 0 0 1px rgba(180,150,60,0.08), 0 32px 80px rgba(0,0,0,0.8), inset 0 1px 0 rgba(180,150,60,0.1);
  position:relative;
  animation: loginFadeIn 0.7s ease forwards;
}
@keyframes loginFadeIn {
  from { opacity:0; transform: translateY(24px); }
  to   { opacity:1; transform: translateY(0); }
}
.login-box::before{
  content:'';position:absolute;top:0;left:48px;right:48px;height:1px;
  background:linear-gradient(90deg, transparent, rgba(180,150,60,0.6), transparent);
}
.login-logo{text-align:center;margin-bottom:36px}
.login-logo img{
  width:160px;height:auto;
  opacity:0.92;
  filter: drop-shadow(0 2px 12px rgba(180,150,60,0.3));
}
.login-title{
  font-family:'Cormorant Garamond',Georgia,serif;
  font-size:13px;font-weight:400;letter-spacing:0.25em;
  color:rgba(180,150,60,0.7);
  text-transform:uppercase;margin-top:20px;
}
.login-sub{font-size:0;margin-top:0}
.login-field-label{
  font-size:10px;font-weight:600;letter-spacing:0.18em;text-transform:uppercase;
  color:rgba(180,150,60,0.5);margin-bottom:8px;display:block;
}
.login-input{
  width:100%;padding:12px 16px;
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(180,150,60,0.2);
  border-radius:2px;
  font-family:'DM Sans',sans-serif;font-size:14px;
  color:rgba(255,255,255,0.85);
  outline:none;
  transition:all 0.2s;
  letter-spacing:0.02em;
}
.login-input::placeholder{color:rgba(255,255,255,0.2)}
.login-input:focus{
  border-color:rgba(180,150,60,0.5);
  background:rgba(255,255,255,0.06);
  box-shadow:0 0 0 3px rgba(180,150,60,0.08);
}
.login-btn{
  width:100%;padding:14px;margin-top:28px;
  background:linear-gradient(135deg, #b8962e 0%, #d4af50 50%, #b8962e 100%);
  border:none;border-radius:2px;cursor:pointer;
  font-family:'DM Sans',sans-serif;font-size:11px;font-weight:700;
  letter-spacing:0.2em;text-transform:uppercase;
  color:#0a0e0a;
  transition:all 0.25s;
  position:relative;overflow:hidden;
}
.login-btn::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
  opacity:0;transition:opacity 0.2s;
}
.login-btn:hover{
  box-shadow:0 4px 24px rgba(180,150,60,0.35);
  transform:translateY(-1px);
}
.login-btn:hover::before{opacity:1}
.login-btn:active{transform:translateY(0)}
.login-error{
  background:rgba(153,27,27,0.15);
  border:1px solid rgba(220,38,38,0.3);
  color:#fca5a5;
  padding:10px 14px;border-radius:2px;
  font-size:12px;margin-top:16px;display:none;
  letter-spacing:0.02em;
}

/* ── Dashboard charts ───────────────────────────────────────────────────── */
.chart-bar-wrap{display:flex;flex-direction:column;gap:8px}
.chart-bar-row{display:flex;align-items:center;gap:8px;font-size:12px}
.chart-bar-label{width:180px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chart-bar-track{flex:1;height:10px;background:var(--bg2);border-radius:5px;overflow:hidden}
.chart-bar-fill{height:100%;background:var(--navy2);border-radius:5px;transition:width .6s ease}
.chart-bar-val{width:30px;text-align:right;color:var(--muted);font-family:'DM Mono',monospace}

/* ── Alertas tabla ──────────────────────────────────────────────────────── */
.alert-row{background:#fffbeb}
.alert-dias{font-weight:700;color:#b45309;font-family:'DM Mono',monospace}

/* ── Toast ──────────────────────────────────────────────────────────────── */
#toast-container{position:fixed;bottom:24px;right:24px;display:flex;flex-direction:column;gap:8px;z-index:9999}
.toast{
  background:var(--navy);color:var(--white);padding:12px 18px;border-radius:9px;
  font-size:13px;box-shadow:var(--shadow-lg);
  animation:toastIn .25s ease;display:flex;align-items:center;gap:8px;
  max-width:320px
}
.toast.success{background:#065f46}
.toast.error{background:#991b1b}
@keyframes toastIn{from{transform:translateX(40px);opacity:0}to{transform:translateX(0);opacity:1}}

/* ── Utilidades ─────────────────────────────────────────────────────────── */
.empty-state{text-align:center;padding:60px 20px;color:var(--muted)}
.empty-state .icon{font-size:40px;margin-bottom:12px}
.loading{text-align:center;padding:40px;color:var(--muted);font-size:13px}
.section-hidden{display:none!important}
.monospace{font-family:'DM Mono',monospace;font-size:12px}
.text-muted{color:var(--muted)}
.flex-1{flex:1}
.gap-8{gap:8px}
</style>
</head>
<body>

<!-- ── LOGIN ──────────────────────────────────────────────────────────────── -->
<div id="login-screen">
  <div class="login-box">
    <div class="login-logo">
      <img src="data:image/png;base64,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" alt="Princess Hotels & Resorts">
      <div class="login-title">Control de Pedidos</div>
    </div>
    <div style="margin-bottom:20px">
      <label class="login-field-label">Usuario</label>
      <input id="login-user" class="login-input" placeholder="usuario" autocomplete="username">
    </div>
    <div>
      <label class="login-field-label">Contraseña</label>
      <input id="login-pass" class="login-input" type="password" autocomplete="current-password">
    </div>
    <div id="login-error" class="login-error"></div>
    <button class="login-btn" onclick="doLogin()">Acceder</button>
  </div>
</div>

<!-- ── APP ────────────────────────────────────────────────────────────────── -->
<div id="app" style="display:none">
  <!-- Sidebar -->
  <div id="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-icon" style="background:none;padding:0;width:48px;height:48px;display:flex;align-items:center;justify-content:center;">
        <img src="data:image/png;base64,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" alt="Princess" style="width:44px;height:44px;object-fit:contain;">
      </div>
      <div>
        <div class="sb-logo-text">Princess</div>
        <div class="sb-logo-sub">Canarias · Compras</div>
      </div>
    </div>

    <div class="sb-section">Principal</div>
    <div class="sb-item active" data-view="dashboard" onclick="showView('dashboard',this)">
      <span class="icon">📊</span> Dashboard
    </div>
    <div class="sb-item" data-view="pedidos" onclick="showView('pedidos',this)">
      <span class="icon">📋</span> Pedidos
    </div>
    <div class="sb-item" data-view="alertas" onclick="showView('alertas',this)">
      <span class="icon">⚠️</span> Alertas
      <span class="sb-badge" id="sb-alert-count" style="display:none">0</span>
    </div>

    <div class="sb-section">Gestión</div>
    <div class="sb-item" data-view="proveedores" onclick="showView('proveedores',this)">
      <span class="icon">🏭</span> Proveedores
    </div>

    <div class="sb-bottom">
      <div class="sb-user">
        <div class="sb-avatar" id="sb-avatar">—</div>
        <div>
          <div class="sb-username" id="sb-nombre">—</div>
          <div class="sb-rol" id="sb-rol">—</div>
        </div>
        <button class="btn btn-ghost btn-sm" style="margin-left:auto;padding:4px 8px;font-size:11px" onclick="doLogout()">Salir</button>
      </div>
    </div>
  </div>

  <!-- Main -->
  <div id="main">
    <div id="topbar">
      <div class="tb-title" id="topbar-title">Dashboard</div>
      <div class="tb-actions">
        <button class="btn btn-ghost btn-sm" onclick="loadStats();loadPedidos()" title="Actualizar">↻ Actualizar</button>
        <button class="btn btn-gold" onclick="openPedidoModal()" id="btn-nuevo-pedido">
          + Nuevo pedido
        </button>
        <button class="btn btn-ghost btn-sm" onclick="exportarExcel()" title="Exportar a Excel">⬇ Excel</button>
        <button class="btn btn-ghost btn-sm" onclick="openImportModal()" title="Importar desde Excel">⬆ Importar</button>
      </div>
    </div>

    <div id="content">

      <!-- VIEW: DASHBOARD ─────────────────────────────────────────────── -->
      <div id="view-dashboard">
        <div class="stats-grid" id="stats-cards">
          <div class="stat-card"><div class="stat-num" id="st-total">—</div><div class="stat-label">Total pedidos</div></div>
          <div class="stat-card"><div class="stat-num" id="st-enviado" style="color:#1e40af">—</div><div class="stat-label">Enviados proveedor</div></div>
          <div class="stat-card"><div class="stat-num" id="st-entregado" style="color:#065f46">—</div><div class="stat-label">Entregados</div></div>
          <div class="stat-card alert-card"><div class="stat-num" id="st-alertas">—</div><div class="stat-label">⚠ Sin resolver +7 días</div></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
          <div class="card">
            <div class="card-header"><span class="card-title">Por estado</span></div>
            <div class="card-body"><div id="chart-estado" class="chart-bar-wrap"></div></div>
          </div>
          <div class="card">
            <div class="card-header"><span class="card-title">Por hotel</span></div>
            <div class="card-body"><div id="chart-hotel" class="chart-bar-wrap"></div></div>
          </div>
        </div>
      </div>

      <!-- VIEW: PEDIDOS ───────────────────────────────────────────────── -->
      <div id="view-pedidos" class="section-hidden">
        <div class="filters">
          <input class="filter-input" id="f-q" placeholder="🔍 Buscar pedido, proveedor…" oninput="debouncedLoad()">
          <select class="filter-select" id="f-hotel" onchange="loadPedidos()">
            <option value="">Todos los hoteles</option>
          </select>
          <select class="filter-select" id="f-estado" onchange="loadPedidos()">
            <option value="">Todos los estados</option>
          </select>
          <select class="filter-select" id="f-depto" onchange="loadPedidos()">
            <option value="">Todos los departamentos</option>
          </select>
          <button class="btn btn-ghost btn-sm" onclick="clearFilters()">✕ Limpiar</button>
        </div>

        <div class="card">
          <div id="pedidos-loading" class="loading">Cargando…</div>
          <div id="pedidos-table-wrap" class="table-wrap" style="display:none">
            <table id="pedidos-table">
              <thead>
                <tr>
                  <th>Nº</th><th>Hotel</th><th>Depto.</th>
                  <th>F. Solicitud</th><th>Pedido SAP</th>
                  <th>Estado</th><th>Proveedor</th>
                  <th>A&B</th><th>Jefe Dep.</th><th>Rotura</th><th>Ampliación</th>
                  <th></th>
                </tr>
              </thead>
              <tbody id="pedidos-tbody"></tbody>
            </table>
          </div>
          <div id="pedidos-empty" class="empty-state section-hidden">
            <div class="icon">📭</div>
            <div>No hay pedidos que mostrar</div>
          </div>
          <div style="padding:12px 20px;border-top:1px solid var(--border)">
            <div style="display:flex;align-items:center">
              <div class="page-info" id="page-info-text"></div>
              <div class="pagination" id="pagination" style="margin-left:auto"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- VIEW: ALERTAS ───────────────────────────────────────────────── -->
      <div id="view-alertas" class="section-hidden">
        <div class="card">
          <div class="card-header">
            <span class="card-title">⚠️ Pedidos sin resolver más de 7 días</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th>Nº</th><th>Hotel</th><th>Pedido SAP</th><th>Estado</th><th>Proveedor</th><th>Días</th><th></th></tr>
              </thead>
              <tbody id="alertas-tbody"></tbody>
            </table>
          </div>
          <div id="alertas-empty" class="empty-state section-hidden">
            <div class="icon">✅</div>
            <div>Sin alertas. ¡Todo al día!</div>
          </div>
        </div>
      </div>

      <!-- VIEW: PROVEEDORES ───────────────────────────────────────────── -->
      <div id="view-proveedores" class="section-hidden">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Proveedores</span>
            <button class="btn btn-gold btn-sm" style="margin-left:auto" onclick="openProveedorModal()">+ Nuevo proveedor</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th>Nombre</th><th>Contacto</th><th>Email</th><th>Teléfono</th><th></th></tr>
              </thead>
              <tbody id="proveedores-tbody"></tbody>
            </table>
          </div>
          <div id="prov-empty" class="empty-state section-hidden">
            <div class="icon">🏭</div><div>No hay proveedores registrados</div>
          </div>
        </div>
      </div>

    </div><!-- /content -->
  </div><!-- /main -->
</div><!-- /app -->

<!-- ── MODAL PEDIDO ─────────────────────────────────────────────────────── -->
<div class="modal-overlay" id="modal-pedido">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title" id="modal-pedido-title">Nuevo pedido</div>
      <button class="close-btn" onclick="closeModal('modal-pedido')">✕</button>
    </div>
    <div class="modal-body">
      <div class="form-grid">
        <!-- Hotel + Departamento -->
        <div class="form-group">
          <label class="form-label">Hotel *</label>
          <select class="form-control" id="p-hotel" required></select>
        </div>
        <div class="form-group">
          <label class="form-label">Departamento *</label>
          <select class="form-control" id="p-depto" required></select>
        </div>

        <!-- Fechas -->
        <div class="form-section">Fechas del flujo</div>
        <div class="form-group">
          <label class="form-label">Fecha solicitud</label>
          <input type="date" class="form-control" id="p-f-solicitud">
        </div>
        <div class="form-group">
          <label class="form-label">Fecha envío Vº Bº</label>
          <input type="date" class="form-control" id="p-f-vb">
        </div>
        <div class="form-group">
          <label class="form-label">Fecha tramitación</label>
          <input type="date" class="form-control" id="p-f-tramit">
        </div>

        <!-- Referencias SAP -->
        <div class="form-section">Referencias SAP</div>
        <div class="form-group">
          <label class="form-label">Pedido Nº (SAP)</label>
          <input class="form-control monospace" id="p-pedido-num" placeholder="Alfanumérico">
        </div>
        <div class="form-group">
          <label class="form-label">Nº Presupuesto</label>
          <input class="form-control monospace" id="p-presup">
        </div>
        <div class="form-group">
          <label class="form-label">Nº Entrada Albarán</label>
          <input class="form-control monospace" id="p-albaran">
        </div>

        <!-- Estado -->
        <div class="form-section">Estado</div>
        <div class="form-group full">
          <label class="form-label">Estado del pedido *</label>
          <select class="form-control" id="p-estado"></select>
        </div>
        <div class="form-group full">
          <label class="form-label">Nota (para historial, opcional)</label>
          <input class="form-control" id="p-nota" placeholder="Motivo del cambio de estado…">
        </div>

        <!-- Proveedor -->
        <div class="form-section">Proveedor</div>
        <div class="form-group full">
          <label class="form-label">Proveedor</label>
          <select class="form-control" id="p-proveedor">
            <option value="">— Sin asignar —</option>
          </select>
        </div>

        <!-- Comunicaciones -->
        <div class="form-section">Comunicaciones y partes</div>
        <div class="form-group full">
          <div class="checkbox-group">
            <label class="checkbox-item"><input type="checkbox" id="p-ab"> Comunicado A&B</label>
            <label class="checkbox-item"><input type="checkbox" id="p-jefe"> Comunicado Jefe Dep.</label>
            <label class="checkbox-item"><input type="checkbox" id="p-rotura"> Parte Rotura y Sustitución</label>
            <label class="checkbox-item"><input type="checkbox" id="p-ampliacion"> Parte Ampliación</label>
          </div>
        </div>

        <!-- Observaciones -->
        <div class="form-section">Observaciones</div>
        <div class="form-group full">
          <textarea class="form-control" id="p-observaciones" rows="3" placeholder="Texto libre…" style="resize:vertical"></textarea>
        </div>
      </div>

      <!-- Historial (solo en edición) -->
      <div id="p-historial-section" style="display:none;margin-top:24px">
        <div style="font-size:11px;font-weight:700;color:var(--navy2);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px">Historial de estados</div>
        <div class="timeline" id="p-historial"></div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-danger btn-sm" id="btn-delete-pedido" style="display:none;margin-right:auto" onclick="deletePedido()">Eliminar</button>
      <button class="btn btn-ghost" onclick="closeModal('modal-pedido')">Cancelar</button>
      <button class="btn btn-gold" onclick="savePedido()" id="btn-save-pedido">Guardar</button>
    </div>
  </div>
</div>

<!-- ── MODAL PROVEEDOR ─────────────────────────────────────────────────── -->
<div class="modal-overlay" id="modal-proveedor">
  <div class="modal" style="max-width:480px">
    <div class="modal-header">
      <div class="modal-title" id="modal-prov-title">Nuevo proveedor</div>
      <button class="close-btn" onclick="closeModal('modal-proveedor')">✕</button>
    </div>
    <div class="modal-body">
      <div class="form-grid" style="grid-template-columns:1fr">
        <div class="form-group">
          <label class="form-label">Nombre *</label>
          <input class="form-control" id="pv-nombre" placeholder="Nombre del proveedor">
        </div>
        <div class="form-group">
          <label class="form-label">Persona de contacto</label>
          <input class="form-control" id="pv-contacto">
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input class="form-control" id="pv-email" type="email">
        </div>
        <div class="form-group">
          <label class="form-label">Teléfono</label>
          <input class="form-control" id="pv-tel">
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="closeModal('modal-proveedor')">Cancelar</button>
      <button class="btn btn-gold" onclick="saveProveedor()">Guardar proveedor</button>
    </div>
  </div>
</div>

<!-- ── TOAST ──────────────────────────────────────────────────────────── -->
<div id="toast-container"></div>

<script>
/* ═══════════════════════════════════════════════════════════════════════════
   Estado global
═══════════════════════════════════════════════════════════════════════════ */
let G = {
  user: null, rol: null,
  maestros: { hoteles:[], departamentos:[], proveedores:[], estados:[] },
  pedidos: [], total: 0, page: 1, pages: 1,
  editingPedidoId: null,
  editingProveedorId: null,
  currentView: 'dashboard',
};

/* ═══════════════════════════════════════════════════════════════════════════
   Auth
═══════════════════════════════════════════════════════════════════════════ */
async function doLogin() {
  const u = document.getElementById('login-user').value.trim();
  const p = document.getElementById('login-pass').value;
  const err = document.getElementById('login-error');
  err.style.display='none';
  try {
    const r = await api('/api/login', 'POST', {username:u, password:p});
    if (r.error) { err.textContent=r.error; err.style.display='block'; return; }
    G.user = r.nombre; G.rol = r.rol;
    document.getElementById('sb-nombre').textContent = r.nombre;
    document.getElementById('sb-rol').textContent    = r.rol === 'admin' ? 'Administrador' : 'Usuario';
    document.getElementById('sb-avatar').textContent = r.nombre.charAt(0).toUpperCase();
    document.getElementById('login-screen').style.display='none';
    document.getElementById('app').style.display='flex';
    if (G.rol !== 'admin') document.getElementById('btn-delete-pedido').style.display='none';
    await loadMaestros();
    showView('dashboard', document.querySelector('[data-view="dashboard"]'));
  } catch(e) { err.textContent='Error de conexión'; err.style.display='block'; }
}

async function doLogout() {
  await api('/api/logout','POST');
  location.reload();
}

document.getElementById('login-pass').addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });
document.getElementById('login-user').addEventListener('keydown', e => { if(e.key==='Enter') document.getElementById('login-pass').focus(); });

/* ═══════════════════════════════════════════════════════════════════════════
   API helper
═══════════════════════════════════════════════════════════════════════════ */
async function api(url, method='GET', body=null) {
  const opts = { method, headers:{'Content-Type':'application/json'}, credentials:'same-origin' };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  return r.json();
}

/* ═══════════════════════════════════════════════════════════════════════════
   Toast
═══════════════════════════════════════════════════════════════════════════ */
function toast(msg, type='') {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = (type==='success'?'✓ ':type==='error'?'✕ ':'')+msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

/* ═══════════════════════════════════════════════════════════════════════════
   Vistas
═══════════════════════════════════════════════════════════════════════════ */
function showView(view, el) {
  document.querySelectorAll('.sb-item').forEach(i=>i.classList.remove('active'));
  if(el) el.classList.add('active');
  document.querySelectorAll('[id^="view-"]').forEach(v=>v.classList.add('section-hidden'));
  document.getElementById(`view-${view}`).classList.remove('section-hidden');
  G.currentView = view;

  const titles = {dashboard:'Dashboard',pedidos:'Pedidos',alertas:'Alertas',proveedores:'Proveedores'};
  document.getElementById('topbar-title').textContent = titles[view]||view;

  if (view==='dashboard')   loadStats();
  if (view==='pedidos')     loadPedidos();
  if (view==='alertas')     loadAlertas();
  if (view==='proveedores') loadProveedores();
}

/* ═══════════════════════════════════════════════════════════════════════════
   Maestros
═══════════════════════════════════════════════════════════════════════════ */
async function loadMaestros() {
  const d = await api('/api/maestros');
  G.maestros = d;

  // Poblar filtros de pedidos
  const fh = document.getElementById('f-hotel');
  d.hoteles.forEach(h => fh.innerHTML += `<option value="${h.id}">${h.codigo} – ${h.nombre}</option>`);

  const fe = document.getElementById('f-estado');
  d.estados.forEach(e => fe.innerHTML += `<option value="${e}">${e}</option>`);

  const fd = document.getElementById('f-depto');
  d.departamentos.forEach(dep => fd.innerHTML += `<option value="${dep.id}">${dep.nombre}</option>`);

  // Poblar selects del modal pedido
  poblarSelectHoteles(); poblarSelectDeptos(); poblarSelectEstados(); poblarSelectProveedores();
}

function poblarSelectHoteles() {
  const s = document.getElementById('p-hotel');
  s.innerHTML = '<option value="">— Selecciona —</option>';
  G.maestros.hoteles.forEach(h => s.innerHTML += `<option value="${h.id}">${h.codigo} – ${h.nombre}</option>`);
}
function poblarSelectDeptos() {
  const s = document.getElementById('p-depto');
  s.innerHTML = '<option value="">— Selecciona —</option>';
  G.maestros.departamentos.forEach(d => s.innerHTML += `<option value="${d.id}">${d.nombre}</option>`);
}
function poblarSelectEstados() {
  const s = document.getElementById('p-estado');
  s.innerHTML = '';
  G.maestros.estados.forEach(e => s.innerHTML += `<option value="${e}">${e}</option>`);
}
function poblarSelectProveedores() {
  const s = document.getElementById('p-proveedor');
  s.innerHTML = '<option value="">— Sin asignar —</option>';
  G.maestros.proveedores.forEach(p => s.innerHTML += `<option value="${p.id}">${p.nombre}</option>`);
}

/* ═══════════════════════════════════════════════════════════════════════════
   Dashboard / Stats
═══════════════════════════════════════════════════════════════════════════ */
async function loadStats() {
  const d = await api('/api/stats');

  document.getElementById('st-total').textContent    = d.total;
  document.getElementById('st-alertas').textContent  = d.num_alertas;

  const envi = d.by_estado.find(e=>e.estado==='ENVIADO AL PROVEEDOR');
  const entr = d.by_estado.find(e=>e.estado==='ENTREGADO');
  document.getElementById('st-enviado').textContent   = envi ? envi.total : 0;
  document.getElementById('st-entregado').textContent = entr ? entr.total : 0;

  // Alerta badge sidebar
  const badge = document.getElementById('sb-alert-count');
  if (d.num_alertas > 0) { badge.textContent=d.num_alertas; badge.style.display=''; }
  else { badge.style.display='none'; }

  // Gráfico estados
  const maxE = Math.max(...d.by_estado.map(e=>e.total), 1);
  document.getElementById('chart-estado').innerHTML = d.by_estado.map(e => `
    <div class="chart-bar-row">
      <div class="chart-bar-label" title="${e.estado}">${e.estado}</div>
      <div class="chart-bar-track"><div class="chart-bar-fill" style="width:${Math.round(e.total/maxE*100)}%"></div></div>
      <div class="chart-bar-val">${e.total}</div>
    </div>`).join('');

  // Gráfico hoteles
  const maxH = Math.max(...d.by_hotel.map(h=>h.total), 1);
  document.getElementById('chart-hotel').innerHTML = d.by_hotel.map(h => `
    <div class="chart-bar-row">
      <div class="chart-bar-label">${h.codigo} – ${h.nombre}</div>
      <div class="chart-bar-track"><div class="chart-bar-fill" style="width:${Math.round(h.total/maxH*100)}%;background:var(--gold)"></div></div>
      <div class="chart-bar-val">${h.total}</div>
    </div>`).join('');
}

/* ═══════════════════════════════════════════════════════════════════════════
   Pedidos
═══════════════════════════════════════════════════════════════════════════ */
let debounceT;
function debouncedLoad() { clearTimeout(debounceT); debounceT=setTimeout(loadPedidos,350); }

async function loadPedidos() {
  const q      = document.getElementById('f-q').value.trim();
  const hotel  = document.getElementById('f-hotel').value;
  const estado = document.getElementById('f-estado').value;
  const depto  = document.getElementById('f-depto').value;
  const params = new URLSearchParams({
    page: G.page, page_size: 20,
    ...(q      && {q}),
    ...(hotel  && {hotel_id:hotel}),
    ...(estado && {estado}),
    ...(depto  && {departamento_id:depto}),
  });

  document.getElementById('pedidos-loading').style.display='';
  document.getElementById('pedidos-table-wrap').style.display='none';
  document.getElementById('pedidos-empty').classList.add('section-hidden');

  const d = await api(`/api/pedidos?${params}`);
  G.pedidos = d.pedidos; G.total = d.total; G.pages = d.pages;

  document.getElementById('pedidos-loading').style.display='none';

  if (!d.pedidos.length) {
    document.getElementById('pedidos-empty').classList.remove('section-hidden');
  } else {
    document.getElementById('pedidos-table-wrap').style.display='';
    renderPedidosTable(d.pedidos);
    renderPagination(d.page, d.pages, d.total);
  }
}

function estadoBadge(estado) {
  const map = {
    'PENDIENTE FIRMA DIRECCION COMPRAS': 'pendiente-compras',
    'PENDIENTE DE FIRMA DIRECCION HOTEL': 'pendiente-hotel',
    'ENVIADO AL PROVEEDOR': 'enviado',
    'ENTREGA PARCIAL': 'parcial',
    'ENTREGADO': 'entregado',
    'ANULADO': 'anulado',
  };
  const cls = map[estado] || 'pendiente-compras';
  return `<span class="badge badge-${cls}">${estado}</span>`;
}

function boolCell(v) {
  return v ? '<span class="bool-si">SÍ</span>' : '<span class="bool-no">—</span>';
}

function renderPedidosTable(pedidos) {
  const tbody = document.getElementById('pedidos-tbody');
  tbody.innerHTML = pedidos.map(p => `
    <tr onclick="openPedidoModal(${p.id})">
      <td class="monospace">${p.norden||'—'}</td>
      <td><strong>${p.hotel_codigo||'—'}</strong></td>
      <td>${p.departamento_nombre||'—'}</td>
      <td>${fmtDate(p.fecha_solicitud)}</td>
      <td class="monospace">${p.pedido_num||'—'}</td>
      <td>${estadoBadge(p.estado)}</td>
      <td>${p.proveedor_nombre||'—'}</td>
      <td>${boolCell(p.comunicado_ab)}</td>
      <td>${boolCell(p.comunicado_jefe_dep)}</td>
      <td>${boolCell(p.parte_rotura)}</td>
      <td>${boolCell(p.parte_ampliacion)}</td>
      <td><button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();openPedidoModal(${p.id})">✏ Editar</button></td>
    </tr>`).join('');
}

function renderPagination(page, pages, total) {
  document.getElementById('page-info-text').textContent = `${total} pedido${total!==1?'s':''}`;
  const el = document.getElementById('pagination');
  let html = `<button class="page-btn" onclick="goPage(${page-1})" ${page<=1?'disabled':''}>‹</button>`;
  for (let i=1; i<=pages; i++) {
    if (pages>7 && i>2 && i<pages-1 && Math.abs(i-page)>1) { if(i===3||i===pages-2) html+='<span class="page-info">…</span>'; continue; }
    html += `<button class="page-btn ${i===page?'active':''}" onclick="goPage(${i})">${i}</button>`;
  }
  html += `<button class="page-btn" onclick="goPage(${page+1})" ${page>=pages?'disabled':''}>›</button>`;
  el.innerHTML = html;
}

function goPage(p) { G.page = p; loadPedidos(); }

function clearFilters() {
  ['f-q','f-hotel','f-estado','f-depto'].forEach(id => {
    const el = document.getElementById(id);
    el.value = '';
  });
  G.page = 1; loadPedidos();
}

/* ═══════════════════════════════════════════════════════════════════════════
   Modal Pedido
═══════════════════════════════════════════════════════════════════════════ */
async function openPedidoModal(id=null) {
  G.editingPedidoId = id;
  clearPedidoForm();
  document.getElementById('modal-pedido-title').textContent = id ? 'Editar pedido' : 'Nuevo pedido';
  document.getElementById('btn-delete-pedido').style.display = (id && G.rol==='admin') ? '' : 'none';
  document.getElementById('p-historial-section').style.display = 'none';

  if (id) {
    const d = await api(`/api/pedidos/${id}`);
    const p = d.pedido;
    setVal('p-hotel', p.hotel_id);
    setVal('p-depto', p.departamento_id);
    setVal('p-f-solicitud', p.fecha_solicitud);
    setVal('p-f-vb', p.fecha_envio_visto_bueno);
    setVal('p-f-tramit', p.fecha_tramitacion);
    setVal('p-pedido-num', p.pedido_num);
    setVal('p-presup', p.presupuesto_num);
    setVal('p-albaran', p.entrada_albaran_num);
    setVal('p-estado', p.estado);
    setVal('p-proveedor', p.proveedor_id||'');
    setVal('p-observaciones', p.observaciones);
    document.getElementById('p-ab').checked       = !!p.comunicado_ab;
    document.getElementById('p-jefe').checked     = !!p.comunicado_jefe_dep;
    document.getElementById('p-rotura').checked   = !!p.parte_rotura;
    document.getElementById('p-ampliacion').checked = !!p.parte_ampliacion;

    // Historial
    if (d.historial && d.historial.length) {
      document.getElementById('p-historial-section').style.display='';
      document.getElementById('p-historial').innerHTML = d.historial.map(h => `
        <div class="tl-item">
          <div class="tl-dot">${h.usuario_nombre?h.usuario_nombre.charAt(0):'?'}</div>
          <div class="tl-content">
            <div class="tl-estado">${h.estado_nuevo}</div>
            <div class="tl-meta">${h.usuario_nombre||'—'} · ${fmtDateTime(h.creado_en)}${h.nota?` · "${h.nota}"`:''}</div>
          </div>
        </div>`).join('');
    }
  }
  openModal('modal-pedido');
}

function clearPedidoForm() {
  ['p-hotel','p-depto','p-pedido-num','p-presup','p-albaran','p-observaciones','p-nota'].forEach(id=>setVal(id,''));
  ['p-f-solicitud','p-f-vb','p-f-tramit'].forEach(id=>setVal(id,''));
  setVal('p-estado', G.maestros.estados[0]||'');
  setVal('p-proveedor','');
  ['p-ab','p-jefe','p-rotura','p-ampliacion'].forEach(id=>document.getElementById(id).checked=false);
}

async function savePedido() {
  const hotel = document.getElementById('p-hotel').value;
  const depto = document.getElementById('p-depto').value;
  if (!hotel) { toast('Selecciona un hotel','error'); return; }

  const body = {
    hotel_id:             hotel,
    departamento_id:      depto || null,
    fecha_solicitud:      val('p-f-solicitud'),
    fecha_envio_visto_bueno: val('p-f-vb'),
    fecha_tramitacion:    val('p-f-tramit'),
    pedido_num:           val('p-pedido-num'),
    presupuesto_num:      val('p-presup'),
    entrada_albaran_num:  val('p-albaran'),
    estado:               val('p-estado'),
    comunicado_ab:        document.getElementById('p-ab').checked,
    comunicado_jefe_dep:  document.getElementById('p-jefe').checked,
    parte_rotura:         document.getElementById('p-rotura').checked,
    parte_ampliacion:     document.getElementById('p-ampliacion').checked,
    proveedor_id:         val('p-proveedor') || null,
    observaciones:        val('p-observaciones'),
    nota_historial:       val('p-nota'),
  };

  const btn = document.getElementById('btn-save-pedido');
  btn.disabled=true; btn.textContent='Guardando…';
  try {
    let r;
    if (G.editingPedidoId) {
      r = await api(`/api/pedidos/${G.editingPedidoId}`, 'PUT', body);
    } else {
      r = await api('/api/pedidos', 'POST', body);
    }
    if (r.error) { toast(r.error,'error'); return; }
    toast(G.editingPedidoId ? 'Pedido actualizado':'Pedido creado', 'success');
    closeModal('modal-pedido');
    if (G.currentView==='pedidos') loadPedidos();
    if (G.currentView==='dashboard') loadStats();
    if (G.currentView==='alertas') loadAlertas();
  } catch(e) { toast('Error de conexión','error'); }
  finally { btn.disabled=false; btn.textContent='Guardar'; }
}

async function deletePedido() {
  if (!confirm('¿Eliminar este pedido? Esta acción no se puede deshacer.')) return;
  const r = await api(`/api/pedidos/${G.editingPedidoId}`, 'DELETE');
  if (r.error) { toast(r.error,'error'); return; }
  toast('Pedido eliminado','success');
  closeModal('modal-pedido');
  loadPedidos(); loadStats();
}

/* ═══════════════════════════════════════════════════════════════════════════
   Alertas
═══════════════════════════════════════════════════════════════════════════ */
async function loadAlertas() {
  const d = await api('/api/stats');
  const tbody = document.getElementById('alertas-tbody');
  const empty = document.getElementById('alertas-empty');
  if (!d.alertas.length) {
    tbody.innerHTML=''; empty.classList.remove('section-hidden'); return;
  }
  empty.classList.add('section-hidden');
  tbody.innerHTML = d.alertas.map(p => `
    <tr class="alert-row">
      <td class="monospace">${p.norden||'—'}</td>
      <td><strong>${p.hotel_codigo||'—'}</strong></td>
      <td class="monospace">${p.pedido_num||'—'}</td>
      <td>${estadoBadge(p.estado)}</td>
      <td>${p.proveedor_nombre||'—'}</td>
      <td class="alert-dias">${calcDias(p.modificado_en)} días</td>
      <td><button class="btn btn-ghost btn-sm" onclick="openPedidoModal(${p.id})">✏ Editar</button></td>
    </tr>`).join('');
}

/* ═══════════════════════════════════════════════════════════════════════════
   Proveedores
═══════════════════════════════════════════════════════════════════════════ */
async function loadProveedores() {
  const d = await api('/api/proveedores');
  const tbody = document.getElementById('proveedores-tbody');
  const empty = document.getElementById('prov-empty');
  if (!d.length) { tbody.innerHTML=''; empty.classList.remove('section-hidden'); return; }
  empty.classList.add('section-hidden');
  tbody.innerHTML = d.map(p => `
    <tr>
      <td><strong>${p.nombre}</strong></td>
      <td>${p.contacto||'—'}</td>
      <td>${p.email||'—'}</td>
      <td>${p.telefono||'—'}</td>
      <td>
        <button class="btn btn-ghost btn-sm" onclick="openProveedorModal(${p.id},'${esc(p.nombre)}','${esc(p.contacto||'')}','${esc(p.email||'')}','${esc(p.telefono||'')}')">✏ Editar</button>
      </td>
    </tr>`).join('');
}

function openProveedorModal(id=null, nombre='', contacto='', email='', tel='') {
  G.editingProveedorId = id;
  document.getElementById('modal-prov-title').textContent = id ? 'Editar proveedor':'Nuevo proveedor';
  setVal('pv-nombre', nombre); setVal('pv-contacto', contacto);
  setVal('pv-email', email); setVal('pv-tel', tel);
  openModal('modal-proveedor');
}

async function saveProveedor() {
  const nombre = val('pv-nombre').trim();
  if (!nombre) { toast('Nombre requerido','error'); return; }
  const body = { nombre, contacto:val('pv-contacto'), email:val('pv-email'), telefono:val('pv-tel') };
  let r;
  if (G.editingProveedorId) {
    r = await api(`/api/proveedores/${G.editingProveedorId}`, 'PUT', body);
  } else {
    r = await api('/api/proveedores', 'POST', body);
    if (r.ok) {
      G.maestros.proveedores.push({id:r.id, nombre});
      poblarSelectProveedores();
    }
  }
  if (r.error) { toast(r.error,'error'); return; }
  toast('Proveedor guardado','success');
  closeModal('modal-proveedor');
  loadProveedores();
  await loadMaestros();
}

/* ═══════════════════════════════════════════════════════════════════════════
   Exportar
═══════════════════════════════════════════════════════════════════════════ */
function exportarExcel() {
  window.open('/api/exportar','_blank');
}

/* ═══════════════════════════════════════════════════════════════════════════
   Modales
═══════════════════════════════════════════════════════════════════════════ */
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
document.querySelectorAll('.modal-overlay').forEach(o =>
  o.addEventListener('click', e => { if(e.target===o) o.classList.remove('open'); })
);
document.addEventListener('keydown', e => {
  if (e.key==='Escape') document.querySelectorAll('.modal-overlay.open').forEach(o=>o.classList.remove('open'));
});

/* ═══════════════════════════════════════════════════════════════════════════
   Utilidades
═══════════════════════════════════════════════════════════════════════════ */
function val(id)       { return document.getElementById(id).value; }
function setVal(id, v) { const el=document.getElementById(id); if(el) el.value=v||''; }
function esc(s)        { return (s||'').replace(/'/g,"\\'"); }

function fmtDate(s) {
  if (!s) return '—';
  try { return new Date(s).toLocaleDateString('es-ES',{day:'2-digit',month:'2-digit',year:'numeric'}); }
  catch { return s; }
}
function fmtDateTime(s) {
  if (!s) return '—';
  try { return new Date(s).toLocaleString('es-ES',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'}); }
  catch { return s; }
}
function calcDias(s) {
  if (!s) return 0;
  return Math.floor((Date.now()-new Date(s).getTime())/(86400000));
}

/* ── Comprobar sesión al cargar ───────────────────────────────────────── */
(async () => {
  const d = await api('/api/me');
  if (d.logged) {
    G.user=d.nombre; G.rol=d.rol;
    document.getElementById('sb-nombre').textContent = d.nombre;
    document.getElementById('sb-rol').textContent    = d.rol==='admin'?'Administrador':'Usuario';
    document.getElementById('sb-avatar').textContent = d.nombre.charAt(0).toUpperCase();
    document.getElementById('login-screen').style.display='none';
    document.getElementById('app').style.display='flex';
    await loadMaestros();
    showView('dashboard', document.querySelector('[data-view="dashboard"]'));
  }
})();
</script>
<!-- ── MODAL IMPORTAR EXCEL ──────────────────────────────────────────────── -->
<div id="import-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center;">
  <div style="background:#fff;border-radius:12px;padding:32px;width:480px;max-width:95vw;box-shadow:0 8px 32px rgba(0,0,0,.2);">
    <h3 style="margin:0 0 8px;color:#0f2044;font-size:1.2rem;">⬆ Importar pedidos desde Excel</h3>
    <p style="margin:0 0 20px;color:#666;font-size:.9rem;">
      El archivo debe tener las mismas columnas que el Excel exportado.<br>
      Los pedidos se <strong>añaden</strong> a los existentes, no se sustituyen.
    </p>

    <div id="import-dropzone"
         style="border:2px dashed #1a3a6b;border-radius:8px;padding:32px;text-align:center;cursor:pointer;transition:.2s;margin-bottom:16px;"
         onclick="document.getElementById('import-file-input').click()"
         ondragover="event.preventDefault();this.style.background='#f0f4ff'"
         ondragleave="this.style.background=''"
         ondrop="handleImportDrop(event)">
      <div style="font-size:2rem;">📂</div>
      <div style="color:#1a3a6b;font-weight:600;margin-top:8px;">Haz clic o arrastra el archivo aquí</div>
      <div id="import-filename" style="color:#888;font-size:.85rem;margin-top:4px;">Ningún archivo seleccionado</div>
    </div>
    <input type="file" id="import-file-input" accept=".xlsx" style="display:none" onchange="handleImportFile(this.files[0])">

    <div id="import-resultado" style="display:none;margin-bottom:16px;padding:12px;border-radius:8px;font-size:.9rem;"></div>

    <div style="display:flex;gap:12px;justify-content:flex-end;">
      <button class="btn btn-ghost btn-sm" onclick="closeImportModal()">Cancelar</button>
      <button class="btn btn-gold" id="btn-importar" onclick="doImport()" disabled style="opacity:.5">Importar</button>
    </div>
  </div>
</div>

<script>
let importFile = null;

function openImportModal() {
  importFile = null;
  document.getElementById('import-filename').textContent = 'Ningún archivo seleccionado';
  document.getElementById('import-resultado').style.display = 'none';
  document.getElementById('import-file-input').value = '';
  const btn = document.getElementById('btn-importar');
  btn.disabled = true; btn.style.opacity = '.5';
  document.getElementById('import-modal').style.display = 'flex';
}

function closeImportModal() {
  document.getElementById('import-modal').style.display = 'none';
}

function handleImportDrop(e) {
  e.preventDefault();
  document.getElementById('import-dropzone').style.background = '';
  const f = e.dataTransfer.files[0];
  if (f) handleImportFile(f);
}

function handleImportFile(f) {
  if (!f || !f.name.endsWith('.xlsx')) {
    alert('Por favor selecciona un archivo .xlsx');
    return;
  }
  importFile = f;
  document.getElementById('import-filename').textContent = f.name;
  document.getElementById('import-resultado').style.display = 'none';
  const btn = document.getElementById('btn-importar');
  btn.disabled = false; btn.style.opacity = '1';
}

async function doImport() {
  if (!importFile) return;
  const btn = document.getElementById('btn-importar');
  btn.disabled = true; btn.textContent = 'Importando…';

  const fd = new FormData();
  fd.append('archivo', importFile);

  try {
    const r = await fetch('/api/importar', { method: 'POST', body: fd });
    const d = await r.json();
    const res = document.getElementById('import-resultado');
    res.style.display = 'block';

    if (d.ok) {
      res.style.background = '#d4edda';
      res.style.color = '#155724';
      let msg = `✅ ${d.insertados} pedido${d.insertados !== 1 ? 's' : ''} importado${d.insertados !== 1 ? 's' : ''} correctamente.`;
      if (d.errores && d.errores.length) {
        msg += `<br><br>⚠️ <strong>${d.errores.length} fila${d.errores.length > 1 ? 's' : ''} con error:</strong><br>` +
               d.errores.map(e => `• ${e}`).join('<br>');
      }
      res.innerHTML = msg;
      loadPedidos(); loadStats();
    } else {
      res.style.background = '#f8d7da';
      res.style.color = '#721c24';
      res.textContent = '❌ Error: ' + d.error;
    }
  } catch(e) {
    const res = document.getElementById('import-resultado');
    res.style.display = 'block';
    res.style.background = '#f8d7da';
    res.style.color = '#721c24';
    res.textContent = '❌ Error de conexión: ' + e.message;
  }

  btn.disabled = false; btn.textContent = 'Importar';
}

// Cerrar modal al hacer clic fuera
document.getElementById('import-modal').addEventListener('click', function(e) {
  if (e.target === this) closeImportModal();
});
</script>

</body>
</html>
