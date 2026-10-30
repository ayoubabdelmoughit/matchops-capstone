with open("dashboard/index.html", "r", encoding="utf-8") as f:
    contenu = f.read()

remplacements = []

# 1. Corriger le port de l'API
ancien = 'const API_BASE = "http://localhost:8020";'
nouveau = 'const API_BASE = "http://localhost:8000";'
contenu, n = contenu.replace(ancien, nouveau), contenu.count(ancien)
remplacements.append(("port API_BASE", n))

# 2. Ajouter le bouton d'onglet "Superviseur"
ancien = '''      <button class="onglet-app" data-vue="gouvernance" style="background:none;border:none;color:var(--muted);font-size:14.5px;font-weight:500;padding:12px 16px;cursor:pointer;border-bottom:2px solid transparent;">Gouvernance</button>
    </div>'''
nouveau = '''      <button class="onglet-app" data-vue="gouvernance" style="background:none;border:none;color:var(--muted);font-size:14.5px;font-weight:500;padding:12px 16px;cursor:pointer;border-bottom:2px solid transparent;">Gouvernance</button>
      <button class="onglet-app" data-vue="superviseur" style="background:none;border:none;color:var(--muted);font-size:14.5px;font-weight:500;padding:12px 16px;cursor:pointer;border-bottom:2px solid transparent;">Superviseur</button>
    </div>'''
n = contenu.count(ancien)
contenu = contenu.replace(ancien, nouveau)
remplacements.append(("bouton onglet", n))

# 3. Ajouter la section "vue-superviseur"
ancien = '''    <div class="vue-app" id="vue-gouvernance" style="display:none;">
      <div class="panel" style="text-align:center; padding:56px 40px; border-style:dashed;">
        <h3>Pas encore connecte</h3>
        <p class="hint">Agent Card, versions SemVer, et bouton de rollback - une fois le depot Git en place.</p>
      </div>
    </div>'''
nouveau = ancien + '''

    <div class="vue-app" id="vue-superviseur" style="display:none;">
      <div class="sec-head"><h2 style="font-size:20px;">Traces d'execution - latence par agent</h2></div>
      <div id="tracesListe" style="display:flex; flex-direction:column; gap:16px;"></div>
    </div>'''
n = contenu.count(ancien)
contenu = contenu.replace(ancien, nouveau)
remplacements.append(("section vue-superviseur", n))

# 4. Ajouter le code JS (rendu des traces + branchement sur le clic d'onglet)
ancien = '''document.querySelectorAll('.onglet-app').forEach(function(btn){
  btn.addEventListener('click', function(){
    document.querySelectorAll('.onglet-app').forEach(function(b){ b.style.color = 'var(--muted)'; b.style.borderBottomColor = 'transparent'; });
    document.querySelectorAll('.vue-app').forEach(function(v){ v.style.display = 'none'; });
    btn.style.color = 'var(--ink)'; btn.style.borderBottomColor = 'var(--accent)';
    document.getElementById('vue-' + btn.dataset.vue).style.display = 'block';
  });
});'''
nouveau = '''document.querySelectorAll('.onglet-app').forEach(function(btn){
  btn.addEventListener('click', function(){
    document.querySelectorAll('.onglet-app').forEach(function(b){ b.style.color = 'var(--muted)'; b.style.borderBottomColor = 'transparent'; });
    document.querySelectorAll('.vue-app').forEach(function(v){ v.style.display = 'none'; });
    btn.style.color = 'var(--ink)'; btn.style.borderBottomColor = 'var(--accent)';
    document.getElementById('vue-' + btn.dataset.vue).style.display = 'block';
    if (btn.dataset.vue === 'superviseur') { chargerTraces(); }
  });
});

function carteTrace(run) {
  var etapes = (run.trace || []).map(function(e){
    var couleur = e.statut === 'ok' ? 'var(--safe)' : 'var(--danger)';
    return '<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;">' +
      '<div style="width:10px;height:10px;border-radius:50%;background:' + couleur + ';"></div>' +
      '<div style="font-family:\\'IBM Plex Mono\\',monospace;font-size:12px;text-align:center;">' + e.agent + '</div>' +
      '<div style="font-size:11.5px;color:var(--muted);">' + e.duree_ms + ' ms</div>' +
      '</div>';
  }).join('<div style="flex:0 0 24px;border-top:2px dashed var(--line);align-self:center;margin-top:5px;"></div>');

  var dureeTotal = (run.trace || []).reduce(function(s, e){ return s + (e.duree_ms || 0); }, 0);

  return '<div style="background:var(--surface);border-radius:10px;padding:20px 24px;">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">' +
    '<div><span style="font-weight:600;">' + run.candidat_id + '</span><span style="color:var(--muted);margin:0 8px;">&rarr;</span><span>' + run.offre_id + '</span></div>' +
    '<div style="display:flex;gap:16px;align-items:center;"><span style="font-family:\\'IBM Plex Mono\\',monospace;color:var(--accent);">score ' + run.score + '</span>' +
    '<span style="font-size:11.5px;color:var(--muted);">' + dureeTotal.toFixed(0) + ' ms total</span></div></div>' +
    (run.trace ? '<div style="display:flex;align-items:flex-start;">' + etapes + '</div>' : '<div class="hint">Pas de trace enregistree pour ce run.</div>') +
    '</div>';
}

function chargerTraces() {
  return fetch(API_BASE + '/supervision/traces', { credentials: 'include' }).then(function(r){ return r.json(); }).then(function(runs){
    document.getElementById('tracesListe').innerHTML = runs.length
      ? runs.map(carteTrace).join('')
      : '<div class="hint" style="padding:20px;background:var(--surface);border-radius:10px;text-align:center;">Aucun run enregistre.</div>';
  });
}'''
n = contenu.count(ancien)
contenu = contenu.replace(ancien, nouveau)
remplacements.append(("JS traces", n))

with open("dashboard/index.html", "w", encoding="utf-8") as f:
    f.write(contenu)

for nom, n in remplacements:
    print(nom, "->", n, "remplacement(s)")