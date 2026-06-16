/* China Power Map — interactive explainer
   Single data model -> three coordinated views: guided tour, explore, roster. */
(async function () {
  const SVGNS = 'http://www.w3.org/2000/svg';
  const $ = (s, r = document) => r.querySelector(s);

  let structure, leadersData, leaders = {};
  try {
    [structure, leadersData] = await Promise.all([
      fetch('../data/china-power-structure.json').then(r => r.json()),
      fetch('../data/china-leaders.json').then(r => r.json())
    ]);
  } catch (e) {
    console.error('China Power Map: failed to load data', e);
    return;
  }
  leadersData.leaders.forEach(l => { leaders[l.slug] = l; });

  /* ---------- small DOM helpers ---------- */
  function el(tag, cls, html) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }
  function svgEl(tag, attrs) {
    const n = document.createElementNS(SVGNS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  function monogram(name) {
    const parts = name.replace(/['']/g, '').split(/\s+/);
    return (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase();
  }

  /* ---------- geometry / anchors ---------- */
  const HH = 22; // default logical half-height for anchor maths
  function anchor(n, side) {
    const hh = n.hh || HH, hw = n.w / 2;
    switch (side) {
      case 'top': return { x: n.x, y: n.y - hh };
      case 'bottom': return { x: n.x, y: n.y + hh };
      case 'left': return { x: n.x - hw, y: n.y };
      case 'right': return { x: n.x + hw, y: n.y };
    }
  }
  // Build a path string for an edge given its route hint.
  function pathFor(a, b, e) {
    const route = e.route || 'curve';
    if (route === 'vert') {
      const up = a.y < b.y ? a : b, dn = a.y < b.y ? b : a;
      const s = anchor(dn, 'top'), t = anchor(up, 'bottom');
      return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
    }
    if (route === 'elbow') {
      const up = a.y < b.y ? a : b, dn = a.y < b.y ? b : a;
      const s = anchor(dn, 'top'), t = anchor(up, 'bottom');
      const my = (s.y + t.y) / 2;
      return `M ${s.x} ${s.y} L ${s.x} ${my} L ${t.x} ${my} L ${t.x} ${t.y}`;
    }
    if (route === 'rail') {
      const railX = e.rail;
      const aSide = railX < a.x ? 'left' : 'right';
      const s = anchor(a, aSide), t = anchor(b, aSide);
      return `M ${s.x} ${s.y} L ${railX} ${s.y} L ${railX} ${t.y} L ${t.x} ${t.y}`;
    }
    if (route === 'arc') {
      const s = anchor(a, 'top'), t = anchor(b, 'top');
      const rise = Math.min(50, Math.abs(t.x - s.x) * 0.10 + 26);
      return `M ${s.x} ${s.y} C ${s.x} ${s.y - rise}, ${t.x} ${t.y - rise}, ${t.x} ${t.y}`;
    }
    // 'curve' — gentle horizontal cubic between facing sides
    const left = a.x <= b.x ? a : b, right = a.x <= b.x ? b : a;
    const s = anchor(left, 'right'), t = anchor(right, 'left');
    const mx = (s.x + t.x) / 2;
    return `M ${s.x} ${s.y} C ${mx} ${s.y}, ${mx} ${t.y}, ${t.x} ${t.y}`;
  }

  /* ---------- renderer ---------- */
  function renderDiagram(canvas, layout, opts = {}) {
    canvas.innerHTML = '';
    canvas.style.paddingBottom = (layout.H / layout.W * 100) + '%';
    const world = el('div', 'cp-world');
    canvas.appendChild(world);
    const svg = svgEl('svg', { class: 'cp-edges', viewBox: `0 0 ${layout.W} ${layout.H}`, preserveAspectRatio: 'none' });
    // arrowhead marker for "nominates" direction
    const defs = svgEl('defs', {});
    const marker = svgEl('marker', { id: 'cp-arrow-' + (opts.id || 'x'), viewBox: '0 0 10 10', refX: '8', refY: '5', markerWidth: '5', markerHeight: '5', orient: 'auto-start-reverse' });
    marker.appendChild(svgEl('path', { d: 'M0,0 L10,5 L0,10 z', fill: 'rgba(244,208,120,0.95)' }));
    defs.appendChild(marker);
    svg.appendChild(defs);
    world.appendChild(svg);

    // faint divider between the two domains
    if (layout.divider != null) {
      svg.appendChild(svgEl('path', { class: 'cp-divider', d: `M ${layout.divider} 8 L ${layout.divider} ${layout.H - 8}` }));
    }

    const nodeById = {};
    layout.nodes.forEach(n => { nodeById[n.id] = n; });

    const edgeRefs = [];
    layout.edges.forEach(e => {
      const a = nodeById[e.from], b = nodeById[e.to];
      if (!a || !b) return;
      let cls = `cp-edge type-${e.type}`;
      if (opts.flow && (e.type === 'approve')) cls += ' flow';
      const attrs = { d: pathFor(a, b, e), class: cls };
      if (e.type === 'nominate') attrs['marker-end'] = `url(#cp-arrow-${opts.id || 'x'})`;
      const p = svgEl('path', attrs);
      svg.appendChild(p);
      edgeRefs.push({ el: p, type: e.type, from: e.from, to: e.to });
    });

    const nodeEls = {};
    layout.nodes.forEach(n => {
      const cls = ['cp-node'];
      if (n.cls) cls.push(n.cls);
      if (n.side) cls.push('side-' + n.side);
      if (n.hub) cls.push('hub');
      if (n.holder) cls.push('has-holder');
      const d = el('div', cls.join(' '), n.label);
      d.style.left = (n.x / layout.W * 100) + '%';
      d.style.top = (n.y / layout.H * 100) + '%';
      d.style.width = (n.w / layout.W * 100) + '%';
      d.dataset.id = n.id;
      if (n.holder) {
        d.dataset.holder = n.holder;
        d.setAttribute('role', 'button');
        d.setAttribute('tabindex', '0');
      }
      world.appendChild(d);
      nodeEls[n.id] = d;
    });

    (layout.headers || []).forEach(h => {
      const d = el('div', 'cp-col-header ' + (h.cls || ''), h.label);
      d.style.left = (h.x / layout.W * 100) + '%';
      d.style.top = (h.y / layout.H * 100) + '%';
      world.appendChild(d);
    });
    (layout.tierLabels || []).forEach(h => {
      const d = el('div', 'cp-tier-label', h.label);
      d.style.left = (h.x / layout.W * 100) + '%';
      d.style.top = (h.y / layout.H * 100) + '%';
      world.appendChild(d);
    });

    return { svg, world, nodeEls, edgeRefs, nodeById, layout };
  }

  /* ---------- national layout (tour) ---------- */
  function nationalLayout() {
    const W = 1100, top = 86, gap = 118;
    const X = { stateSpine: 300, cmcPrc: 470, cmcCcp: 630, partySpine: 800 };
    const Y = s => top + s * gap;
    const wide = 200, std = 170, cmc = 150;
    const pos = {
      'n-president':    { x: X.stateSpine, y: Y(0), w: std, holder: 'xi-jinping' },
      'n-cmc-prc':      { x: X.cmcPrc,     y: Y(0), w: cmc, holder: 'xi-jinping' },
      'n-premier':      { x: X.stateSpine, y: Y(1), w: std, cls: 'role', holder: 'li-qiang' },
      'n-statecouncil': { x: X.stateSpine, y: Y(2), w: std },
      'n-npcsc':        { x: X.stateSpine, y: Y(3), w: std, cls: 'soft', holder: 'zhao-leji' },
      'n-npc':          { x: X.stateSpine, y: Y(4), w: wide, cls: 'big' },
      'n-cmc-ccp':      { x: X.cmcCcp,     y: Y(0), w: cmc, holder: 'xi-jinping' },
      'n-gensec':       { x: X.partySpine, y: Y(0), w: std, cls: 'big', holder: 'xi-jinping' },
      'n-psc':          { x: X.partySpine, y: Y(1), w: std, cls: 'soft' },
      'n-politburo':    { x: X.partySpine, y: Y(2), w: std },
      'n-cc':           { x: X.partySpine, y: Y(3), w: std },
      'n-npcongress':   { x: X.partySpine, y: Y(4), w: wide, cls: 'big' }
    };
    const hubs = new Set(['n-gensec', 'n-psc', 'n-president']);
    const nodes = structure.national.nodes.map(n => Object.assign(
      { id: n.id, label: n.label, side: n.side, hub: hubs.has(n.id),
        cls: n.big ? 'big' : (n.soft ? 'soft' : (n.role ? 'role' : '')) },
      pos[n.id], { holder: pos[n.id].holder }));

    const route = {
      'same': (a, b) => (Math.abs(a.x - b.x) > 300 ? 'arc' : 'curve'),
    };
    const railL = 120, railR = 980;
    const edges = structure.national.edges.map(e => {
      const a = pos[e.from], b = pos[e.to];
      let r;
      if (e.type === 'same') r = route.same(a, b);
      else if (e.type === 'member' || e.type === 'nominate') r = 'curve';
      else { // approve
        if (Math.abs(a.x - b.x) < 5 && Math.abs(a.y - b.y) <= gap + 2) r = 'vert';
        else if (Math.abs(a.x - b.x) < 5) return { from: e.from, to: e.to, type: e.type, route: 'rail', rail: a.x < W / 2 ? railL : railR };
        else r = 'curve';
      }
      return { from: e.from, to: e.to, type: e.type, route: r };
    });

    return {
      W, H: Y(4) + 60, nodes, edges, divider: W / 2,
      headers: [
        { x: X.cmcPrc - 60, y: 30, label: structure.national.state_header, cls: 'h-state' },
        { x: X.cmcCcp + 60, y: 30, label: structure.national.party_header, cls: 'h-party' }
      ]
    };
  }

  /* ---------- full layout (explore) ---------- */
  function fullLayout() {
    const W = 1120, top = 140, tierH = 158;
    const levels = [{ key: 'national', name: 'National', gov_leader: 'President', congress: "National People's Congress", committee: 'Central Committee', secretary: 'General Secretary' }]
      .concat(structure.levels.map(l => ({
        key: l.key, name: l.name, gov_leader: l.gov_leader,
        congress: l.congress, committee: l.name + ' Party Committee', secretary: 'Party Secretary'
      })));

    const X = { govChip: 340, congress: 310, secChip: 780, committee: 810 };
    const nodes = [], edges = [], tierLabels = [];
    const railL = 120, railR = 1000;

    levels.forEach((lv, i) => {
      const tTop = top + i * tierH;
      const govId = `f-gov-${i}`, conId = `f-con-${i}`, secId = `f-sec-${i}`, comId = `f-com-${i}`;
      nodes.push({ id: govId, x: X.govChip, y: tTop, w: 160, cls: 'role', side: 'state', label: lv.gov_leader, hh: 18, holder: i === 0 ? 'xi-jinping' : null });
      nodes.push({ id: conId, x: X.congress, y: tTop + 82, w: 220, cls: 'big', side: 'state', label: lv.congress, holder: i === 0 ? 'zhao-leji' : null });
      nodes.push({ id: secId, x: X.secChip, y: tTop, w: 175, cls: 'soft', side: 'party', hub: i === 0, label: lv.secretary, hh: 18, holder: i === 0 ? 'xi-jinping' : null });
      nodes.push({ id: comId, x: X.committee, y: tTop + 82, w: 220, cls: 'big', side: 'party', label: lv.committee });
      tierLabels.push({ x: 44, y: tTop + 40, label: lv.name });

      // within-tier
      edges.push({ from: conId, to: govId, type: 'approve', route: 'elbow' });
      edges.push({ from: comId, to: secId, type: 'approve', route: 'elbow' });
      edges.push({ from: comId, to: govId, type: 'nominate', route: 'curve' });

      // climb up to the level above
      if (i > 0) {
        edges.push({ from: conId, to: `f-con-${i - 1}`, type: 'approve', route: 'rail', rail: railL });
        edges.push({ from: comId, to: `f-com-${i - 1}`, type: 'approve', route: 'rail', rail: railR });
      }
    });

    // base
    const bTop = top + levels.length * tierH;
    nodes.push({ id: 'b-citizens', x: X.congress, y: bTop + 18, w: 220, cls: 'big', side: 'state', label: structure.base.state.label });
    nodes.push({ id: 'b-members', x: X.committee, y: bTop + 18, w: 220, cls: 'big', side: 'party', label: structure.base.party.label });
    tierLabels.push({ x: 44, y: bTop + 18, label: 'Base' });
    edges.push({ from: 'b-citizens', to: `f-con-${levels.length - 1}`, type: 'approve', route: 'vert' });
    edges.push({ from: 'b-members', to: `f-com-${levels.length - 1}`, type: 'approve', route: 'vert' });

    // national personal union
    edges.push({ from: 'f-gov-0', to: 'f-sec-0', type: 'same', route: 'arc' });

    return {
      W, H: bTop + 70, nodes, edges, tierLabels, divider: W / 2,
      headers: [
        { x: X.govChip, y: 50, label: 'The State', cls: 'h-state' },
        { x: X.secChip, y: 50, label: 'The Party', cls: 'h-party' }
      ]
    };
  }

  /* ---------- profile panel ---------- */
  const overlay = $('#cp-overlay'), panel = $('#cp-panel');
  function openProfile(slug) {
    const l = leaders[slug];
    if (!l) return;
    const photo = $('#cp-panel-photo');
    photo.innerHTML = `<div class="cp-panel-frame"><span class="cp-panel-mono">${monogram(l.name)}</span></div>`;
    const flag = l.status && l.status !== 'active'
      ? `<div class="cp-status-flag">${l.status_note || 'Status changed'}</div>` : '';
    $('#cp-panel-content').innerHTML =
      `<div class="cp-rank-badge">#${l.rank} · ${l.body}</div>
       <h3>${l.name}</h3>
       <div class="cp-panel-title">${l.title}</div>
       ${flag}
       <p class="cp-panel-bio">${l.bio}</p>`;
    overlay.classList.add('open');
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false');
  }
  function closeProfile() {
    overlay.classList.remove('open');
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
  }
  overlay.addEventListener('click', closeProfile);
  $('#cp-panel-close').addEventListener('click', closeProfile);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeProfile(); });

  function wireHolders(refs) {
    Object.values(refs.nodeEls).forEach(node => {
      if (!node.dataset.holder) return;
      node.addEventListener('click', () => openProfile(node.dataset.holder));
      node.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openProfile(node.dataset.holder); } });
    });
  }

  /* ---------- TOUR ---------- */
  function buildTour() {
    const canvas = $('#cp-tour-canvas');
    const layout = nationalLayout();
    const refs = renderDiagram(canvas, layout, { id: 'tour' });
    wireHolders(refs);

    // measure path lengths for draw-on (skip dashed nominate lines)
    refs.edgeRefs.forEach(e => {
      try {
        e.len = e.el.getTotalLength();
        if (e.type !== 'nominate' && e.len) {
          e.el.style.strokeDasharray = e.len;
          e.el.style.strokeDashoffset = e.len;
        }
      } catch (_) { e.len = 0; }
    });

    const stepsWrap = $('#cp-steps');
    structure.tour.forEach((s, i) => {
      const step = el('div', 'cp-step');
      step.dataset.idx = i;
      step.innerHTML =
        `<div class="cp-step-card">
           <div class="cp-step-num">Step ${i + 1} of ${structure.tour.length}</div>
           <h3>${s.title}</h3>
           <p>${s.body}</p>
         </div>`;
      stepsWrap.appendChild(step);
    });

    const pulseIds = ['n-president', 'n-cmc-prc', 'n-cmc-ccp', 'n-gensec'];

    // cinematic camera: frame a set of nodes within the canvas viewport
    const wide = () => window.matchMedia('(min-width: 721px)').matches;
    function frame(nodeIds, full) {
      const cw = canvas.clientWidth, ch = canvas.clientHeight;
      if (!cw || !ch) return;
      const px = cw / layout.W, py = ch / layout.H;
      // logical bounding box to frame
      let minx, miny, maxx, maxy;
      if (full || !nodeIds || !nodeIds.length) {
        minx = 0; miny = 0; maxx = layout.W; maxy = layout.H;
      } else {
        minx = Infinity; miny = Infinity; maxx = -Infinity; maxy = -Infinity;
        nodeIds.forEach(id => {
          const n = refs.nodeById[id]; if (!n) return;
          minx = Math.min(minx, n.x - n.w / 2); maxx = Math.max(maxx, n.x + n.w / 2);
          miny = Math.min(miny, n.y - (n.hh || 22)); maxy = Math.max(maxy, n.y + (n.hh || 22));
        });
        if (minx === Infinity) { minx = 0; miny = 0; maxx = layout.W; maxy = layout.H; }
        minx -= layout.W * 0.04; maxx += layout.W * 0.04;
        miny -= layout.H * 0.09; maxy += layout.H * 0.09;
      }
      const rx = minx * px, ry = miny * py, rw = (maxx - minx) * px, rh = (maxy - miny) * py;
      // reserve a safe area on the left for the floating narrative card (desktop only)
      const leftInset = wide() ? Math.min(cw * 0.30, 440) : 0;
      const topInset = wide() ? 0 : ch * 0.04;
      const aw = cw - leftInset, ah = ch - topInset, acx = leftInset + aw / 2, acy = topInset + ah / 2;
      let s = Math.min(aw / rw, ah / rh);
      s = full ? Math.min(s, 1.0) : Math.min(s, 2.2);
      s = Math.max(0.45, s);
      const tx = acx - s * (rx + rw / 2), ty = acy - s * (ry + rh / 2);
      refs.world.style.transform = `translate(${tx}px, ${ty}px) scale(${s})`;
    }

    function applyStep(i) {
      const s = structure.tour[i];
      const full = s.scope === 'full' || (!s.focus);
      let litNodes = full ? new Set(Object.keys(refs.nodeEls)) : new Set(s.focus);

      Object.entries(refs.nodeEls).forEach(([id, n]) => {
        n.classList.toggle('lit', litNodes.has(id));
        n.classList.toggle('pulse', s.id === 'same' && pulseIds.includes(id));
      });

      refs.edgeRefs.forEach(e => {
        let lit = false;
        if (s.scope === 'full') lit = true;
        else if (s.edge_types) lit = s.edge_types.includes(e.type) && litNodes.has(e.from) && litNodes.has(e.to);
        else if (s.focus) lit = litNodes.has(e.from) && litNodes.has(e.to);
        e.el.classList.toggle('lit', lit);
        if (e.type !== 'nominate' && e.len) e.el.style.strokeDashoffset = lit ? '0' : e.len;
      });

      frame(full ? null : s.focus, full);
    }

    const steps = Array.from(stepsWrap.children);
    let current = -1;
    function setActive(i) {
      if (i === current) return;
      current = i;
      steps.forEach((st, k) => st.classList.toggle('is-active', k === i));
      applyStep(i);
    }
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => { if (en.isIntersecting) setActive(+en.target.dataset.idx); });
    }, { rootMargin: '-50% 0px -50% 0px', threshold: 0 });
    steps.forEach(st => io.observe(st));

    let rt;
    window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => current >= 0 && applyStep(current), 200); });
    // initial draw once layout has measured size
    requestAnimationFrame(() => setActive(0));
  }

  /* ---------- EXPLORE ---------- */
  function buildExplore() {
    const canvas = $('#cp-explore-canvas');
    const refs = renderDiagram(canvas, fullLayout(), { flow: true, id: 'explore' });
    wireHolders(refs);

    // neighbour map
    const neighbours = {};
    refs.edgeRefs.forEach(e => {
      (neighbours[e.from] = neighbours[e.from] || new Set()).add(e.to);
      (neighbours[e.to] = neighbours[e.to] || new Set()).add(e.from);
    });

    function highlightNode(id) {
      canvas.classList.add('dimming');
      const keep = new Set([id, ...(neighbours[id] || [])]);
      Object.entries(refs.nodeEls).forEach(([nid, n]) => n.classList.toggle('hl', keep.has(nid)));
      refs.edgeRefs.forEach(e => e.el.classList.toggle('hl', e.from === id || e.to === id));
    }
    function clearHighlight() {
      canvas.classList.remove('dimming');
      Object.values(refs.nodeEls).forEach(n => n.classList.remove('hl'));
      refs.edgeRefs.forEach(e => e.el.classList.remove('hl'));
    }
    Object.entries(refs.nodeEls).forEach(([id, n]) => {
      n.addEventListener('mouseenter', () => highlightNode(id));
      n.addEventListener('mouseleave', clearHighlight);
    });

    // legend
    const legend = $('#cp-legend');
    const active = new Set(structure.relationship_types.map(t => t.id));
    function applyTypes() {
      refs.edgeRefs.forEach(e => e.el.classList.toggle('type-hidden', !active.has(e.type)));
    }
    structure.relationship_types.forEach(t => {
      const item = el('div', 'cp-legend-item', `<span class="cp-legend-swatch sw-${t.id}"></span><span>${t.label}</span>`);
      item.title = t.desc;
      item.addEventListener('click', () => {
        if (active.has(t.id)) active.delete(t.id); else active.add(t.id);
        item.classList.toggle('off', !active.has(t.id));
        applyTypes();
      });
      item.addEventListener('mouseenter', () => {
        if (!active.has(t.id)) return;
        canvas.classList.add('dimming');
        refs.edgeRefs.forEach(e => e.el.classList.toggle('hl', e.type === t.id));
      });
      item.addEventListener('mouseleave', clearHighlight);
      legend.appendChild(item);
    });
    legend.insertAdjacentHTML('beforeend', '<span class="cp-legend-hint">Toggle a relationship to filter · hover to trace</span>');
  }

  /* ---------- ROSTER ---------- */
  function buildRoster() {
    const wrap = $('#cp-roster');
    const groups = [
      { title: 'Standing Committee', sub: 'The seven who decide — ranked in protocol order.', body: 'Politburo Standing Committee' },
      { title: 'The wider Politburo', sub: 'The remaining members, in approximate order of seniority.', body: 'Politburo' }
    ];
    groups.forEach(g => {
      const members = leadersData.leaders.filter(l => l.body === g.body).sort((a, b) => a.rank - b.rank);
      const gWrap = el('div', 'cp-roster-group');
      gWrap.appendChild(el('div', 'cp-roster-grouptitle', g.title));
      gWrap.appendChild(el('div', 'cp-roster-groupsub', g.sub));
      const grid = el('div', 'cp-roster');
      members.forEach(l => {
        const flagged = l.status && l.status !== 'active';
        const card = el('button', 'cp-card' + (flagged ? ' flagged' : ''));
        if (flagged) card.title = l.status_note || '';
        card.innerHTML =
          `<span class="cp-card-rank">${l.rank}</span>
           <span class="cp-card-frame"><span class="cp-card-mono">${monogram(l.name)}</span></span>
           <span class="cp-card-info">
             <span class="cp-card-name">${l.name}</span>
             <span class="cp-card-role">${l.short_title}</span>
           </span>`;
        card.addEventListener('click', () => openProfile(l.slug));
        grid.appendChild(card);
      });
      gWrap.appendChild(grid);
      wrap.appendChild(gWrap);
    });
    $('#cp-roster-note').innerHTML = `<strong>A note on ranking and currency.</strong> ${leadersData.note} Leadership shown as of ${leadersData.as_of_pretty}; officials under investigation or removed are flagged.`;
    $('#cp-asof-label').textContent = leadersData.as_of_pretty;
  }

  /* ---------- scroll reveals ---------- */
  function buildReveals() {
    const targets = document.querySelectorAll('.cp-section-head, .cp-roster-group, .cp-explore-toolbar, .cp-explore-canvas, .cp-note');
    targets.forEach(t => t.classList.add('cp-reveal'));
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });
    targets.forEach(t => io.observe(t));
  }

  /* ---------- go ---------- */
  buildTour();
  buildExplore();
  buildRoster();
  buildReveals();
})();
