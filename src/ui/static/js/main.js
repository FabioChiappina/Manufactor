// Main JavaScript for Manufactor Flask UI

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Card sort, group, and filter controls
    const sortSelect = document.getElementById('sort-select');
    const groupSelect = document.getElementById('group-select');
    const mvOpSelect = document.getElementById('mv-op-select');
    const mvValueInput = document.getElementById('mv-value-input');
    const typeFilterSelect = document.getElementById('type-filter-select');
    if (sortSelect && groupSelect) {
        sortSelect.addEventListener('change', applyCardControls);
        groupSelect.addEventListener('change', applyCardControls);
        if (mvOpSelect) mvOpSelect.addEventListener('change', applyCardControls);
        if (mvValueInput) mvValueInput.addEventListener('input', applyCardControls);
        if (typeFilterSelect) typeFilterSelect.addEventListener('change', applyCardControls);
        // Apply defaults immediately on page load
        applyCardControls();
    }

    // Render deck charts if present (deferred so layout is settled)
    if (document.getElementById('manaCurveChart') || document.getElementById('typeBreakdownChart')) {
        requestAnimationFrame(function() { renderDeckCharts(); });
    }

    // Floating scroll navigation buttons
    const scrollTopBtn = document.getElementById('scroll-top-btn');
    const scrollNextGroupBtn = document.getElementById('scroll-next-group-btn');
    const scrollBottomBtn = document.getElementById('scroll-bottom-btn');

    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
    if (scrollNextGroupBtn) {
        scrollNextGroupBtn.addEventListener('click', function() {
            const headers = Array.from(document.querySelectorAll('.card-group-header'));
            if (!headers.length) return;
            const next = headers.find(function(h) {
                return h.getBoundingClientRect().top > 10;
            });
            if (next) {
                next.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }
    if (scrollBottomBtn) {
        scrollBottomBtn.addEventListener('click', function() {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        });
    }
});

// --- Card Sort & Group ---

// Snapshot of the original card elements, captured once on first call.
// Using a canonical list prevents tag-grouping clones from being double-counted
// on subsequent group-by changes.
let _canonicalCardItems = null;

function getCanonicalItems() {
    if (!_canonicalCardItems) {
        _canonicalCardItems = Array.from(document.querySelectorAll('.card-gallery-item'));
    }
    return _canonicalCardItems;
}

function getManaValue(cost) {
    if (!cost) return 0;
    let cmc = 0;
    const matches = cost.match(/\{([^}]+)\}/g) || [];
    for (const sym of matches) {
        const inner = sym.slice(1, -1).toUpperCase();
        const num = parseInt(inner, 10);
        if (!isNaN(num)) {
            cmc += num;
        } else if (inner === 'X' || inner === 'Y' || inner === 'Z') {
            // variable mana counts as 0
        } else {
            // colour pip, hybrid, phyrexian, snow — each counts as 1
            cmc += 1;
        }
    }
    return cmc;
}

const TYPE_ORDER = ['Creature', 'Planeswalker', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Land', 'Battle', 'Other'];

// --- Color grouping helpers ---

const WUBRG_LETTERS = ['W', 'U', 'B', 'R', 'G'];

// Maps WUBRG-sorted color key → display name.
// Keys are ordered from fewest to most colors, then WUBRG within each tier.
const COLOR_NAMES = {
    '':      'Colorless',
    'W':     'White',
    'U':     'Blue',
    'B':     'Black',
    'R':     'Red',
    'G':     'Green',
    'WU':    'Azorius',
    'WB':    'Orzhov',
    'WR':    'Boros',
    'WG':    'Selesnya',
    'UB':    'Dimir',
    'UR':    'Izzet',
    'UG':    'Simic',
    'BR':    'Rakdos',
    'BG':    'Golgari',
    'RG':    'Gruul',
    'WUB':   'Esper',
    'WUR':   'Jeskai',
    'WUG':   'Bant',
    'WBR':   'Mardu',
    'WBG':   'Abzan',
    'WRG':   'Naya',
    'UBR':   'Grixis',
    'UBG':   'Sultai',
    'URG':   'Temur',
    'BRG':   'Jund',
    'WUBR':  'Yore-Tiller',
    'WUBG':  'Witch-Maw',
    'WURG':  'Ink-Treader',
    'WBRG':  'Dune-Brood',
    'UBRG':  'Glint-Eye',
    'WUBRG': 'Five-Color'
};

const COLOR_KEY_ORDER = Object.keys(COLOR_NAMES);

function getColorsFromCost(cost) {
    if (!cost) return [];
    const found = new Set();
    const matches = cost.match(/\{([^}]+)\}/g) || [];
    for (const sym of matches) {
        const inner = sym.slice(1, -1).toUpperCase();
        // Handle hybrid {W/U}, phyrexian {W/P}, and two-cost {2/W}
        const parts = inner.includes('/') ? inner.split('/') : [inner];
        for (const p of parts) {
            if (WUBRG_LETTERS.includes(p)) found.add(p);
        }
    }
    // Return in WUBRG order
    return WUBRG_LETTERS.filter(function(c) { return found.has(c); });
}

function normalizeCardType(cardtype) {
    if (!cardtype) return ['Other'];
    const ct = cardtype.toLowerCase();
    const matches = TYPE_ORDER.filter(function(t) { return ct.includes(t.toLowerCase()); });
    return matches.length > 0 ? matches : ['Other'];
}

function matchesManaFilter(item, op, value) {
    if (op === 'any') return true;
    if (value === '' || value === null) return true;
    const mv = getManaValue(item.dataset.cost);
    const v = parseInt(value, 10);
    if (isNaN(v)) return true;
    if (op === 'lt') return mv < v;
    if (op === 'eq') return mv === v;
    if (op === 'gt') return mv > v;
    return true;
}

function matchesTypeFilter(item, typeFilter) {
    if (typeFilter === 'any') return true;
    const ct = (item.dataset.cardtype || '').toLowerCase();
    switch (typeFilter) {
        case 'creature':           return ct.includes('creature');
        case 'artifact':           return ct.includes('artifact');
        case 'enchantment':        return ct.includes('enchantment');
        case 'land':               return ct.includes('land');
        case 'instant':            return ct.includes('instant');
        case 'sorcery':            return ct.includes('sorcery');
        case 'instant-sorcery':    return ct.includes('instant') || ct.includes('sorcery');
        case 'planeswalker':       return ct.includes('planeswalker');
        case 'nonland':            return !ct.includes('land');
        case 'noncreature-nonland':return !ct.includes('creature') && !ct.includes('land');
        case 'other':
            return !ct.includes('creature') && !ct.includes('artifact') &&
                   !ct.includes('enchantment') && !ct.includes('land') &&
                   !ct.includes('instant') && !ct.includes('sorcery') &&
                   !ct.includes('planeswalker');
        default: return true;
    }
}

function applyCardControls() {
    const sortSelect = document.getElementById('sort-select');
    const groupSelect = document.getElementById('group-select');
    const cardList = document.querySelector('.card-list');
    if (!sortSelect || !groupSelect || !cardList) return;

    const sortBy = sortSelect.value;
    const groupBy = groupSelect.value;

    // Read filter values
    const mvOpEl = document.getElementById('mv-op-select');
    const mvValEl = document.getElementById('mv-value-input');
    const typeFilterEl = document.getElementById('type-filter-select');
    const mvOp = mvOpEl ? mvOpEl.value : 'any';
    const mvValue = mvValEl ? mvValEl.value : '';
    const typeFilter = typeFilterEl ? typeFilterEl.value : 'any';

    // Always work from the canonical snapshot, not whatever is currently in the DOM
    // (tag grouping leaves clones in the DOM that would inflate counts otherwise)
    const allItems = [...getCanonicalItems()];
    if (!allItems.length) return;

    // Apply filters
    const filteredItems = allItems.filter(function(item) {
        return matchesManaFilter(item, mvOp, mvValue) && matchesTypeFilter(item, typeFilter);
    });

    // Update the "Cards (N)" header to reflect filtered count
    const cardsCountHeader = document.getElementById('cards-count-header');
    if (cardsCountHeader) {
        const totalFilteredQty = filteredItems.reduce(function(sum, item) {
            return sum + parseInt(item.dataset.quantity || '1', 10);
        }, 0);
        cardsCountHeader.textContent = 'Cards (' + totalFilteredQty + ')';
    }

    // Sort
    filteredItems.sort(function(a, b) {
        if (sortBy === 'mana') {
            const mvA = getManaValue(a.dataset.cost);
            const mvB = getManaValue(b.dataset.cost);
            // CMC 0 (lands, X-spells, etc.) sorts to the very end
            const sortA = mvA === 0 ? Number.MAX_SAFE_INTEGER : mvA;
            const sortB = mvB === 0 ? Number.MAX_SAFE_INTEGER : mvB;
            if (sortA !== sortB) return sortA - sortB;
        }
        return (a.dataset.name || '').localeCompare(b.dataset.name || '');
    });

    // Tear down existing galleries / groups
    cardList.querySelectorAll('.card-gallery, .card-group').forEach(function(el) { el.remove(); });

    if (groupBy === 'none') {
        const gallery = document.createElement('div');
        gallery.className = 'card-gallery';
        filteredItems.forEach(function(item) { gallery.appendChild(item); });
        cardList.appendChild(gallery);
        return;
    }

    // Build group map
    const groupMap = new Map();

    filteredItems.forEach(function(item) {
        let keys;
        if (groupBy === 'type') {
            keys = normalizeCardType(item.dataset.cardtype);
        } else if (groupBy === 'landnonland') {
            const ct = (item.dataset.cardtype || '').toLowerCase();
            keys = [ct.includes('land') ? 'Land' : 'Nonland'];
        } else if (groupBy === 'color') {
            // Key is the WUBRG-sorted color string ('WU', 'R', '' for colorless, etc.)
            keys = [getColorsFromCost(item.dataset.cost).join('')];
        } else {
            // tag
            const tagStr = (item.dataset.tags || '').trim();
            const tags = tagStr ? tagStr.split(',').map(function(t) { return t.trim(); }).filter(Boolean) : [];
            keys = tags.length > 0 ? tags : ['Untagged'];
        }

        keys.forEach(function(key, i) {
            if (!groupMap.has(key)) groupMap.set(key, []);
            // Clone the element when a card belongs to multiple groups
            const el = (i < keys.length - 1) ? item.cloneNode(true) : item;
            groupMap.get(key).push(el);
        });
    });

    // Sort group keys
    let groupKeys = Array.from(groupMap.keys());
    if (groupBy === 'type') {
        groupKeys.sort(function(a, b) {
            const ia = TYPE_ORDER.indexOf(a);
            const ib = TYPE_ORDER.indexOf(b);
            return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib);
        });
    } else if (groupBy === 'landnonland') {
        // Nonland first, Land second
        groupKeys.sort(function(a) { return a === 'Nonland' ? -1 : 1; });
    } else if (groupBy === 'color') {
        groupKeys.sort(function(a, b) {
            if (a === '' && b !== '') return 1;   // Colorless always last
            if (b === '' && a !== '') return -1;
            const ia = COLOR_KEY_ORDER.indexOf(a);
            const ib = COLOR_KEY_ORDER.indexOf(b);
            return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib);
        });
    } else {
        groupKeys.sort(function(a, b) {
            if (a === 'Untagged') return 1;
            if (b === 'Untagged') return -1;
            return a.localeCompare(b);
        });
    }

    // Render groups
    groupKeys.forEach(function(key) {
        const items = groupMap.get(key);
        const groupEl = document.createElement('div');
        groupEl.className = 'card-group';

        const totalQty = items.reduce(function(sum, item) {
            return sum + parseInt(item.dataset.quantity || '1', 10);
        }, 0);
        const displayKey = (groupBy === 'color')
            ? (COLOR_NAMES[key] !== undefined ? COLOR_NAMES[key] : key || 'Colorless')
            : key;
        const header = document.createElement('h4');
        header.className = 'card-group-header';
        header.textContent = displayKey + ' (' + totalQty + ')';
        groupEl.appendChild(header);

        const gallery = document.createElement('div');
        gallery.className = 'card-gallery';
        items.forEach(function(item) { gallery.appendChild(item); });
        groupEl.appendChild(gallery);

        cardList.appendChild(groupEl);
    });
}

// ─── Deck Charts ──────────────────────────────────────────────────────────────

var _chartResizeTimer = null;
window.addEventListener('resize', function() {
    clearTimeout(_chartResizeTimer);
    _chartResizeTimer = setTimeout(renderDeckCharts, 150);
});

function renderDeckCharts() {
    var manaCurveCanvas = document.getElementById('manaCurveChart');
    var typeCanvas = document.getElementById('typeBreakdownChart');
    if (!manaCurveCanvas && !typeCanvas) return;

    // Use canonical items so we always see the full deck regardless of filters
    var items = getCanonicalItems();

    var manaCurve = {}; // { mv: { permanents: N, spells: N } }
    var typeCounts = {
        'Creature': 0, 'Artifact': 0, 'Enchantment': 0,
        'Instant': 0, 'Sorcery': 0, 'Planeswalker': 0,
        'Land': 0, 'Other': 0
    };

    items.forEach(function(item) {
        var cost    = item.dataset.cost     || '';
        var cardtype = item.dataset.cardtype || '';
        var qty     = parseInt(item.dataset.quantity, 10) || 1;
        var ct      = cardtype.toLowerCase();

        var isCreature     = ct.includes('creature');
        var isArtifact     = ct.includes('artifact');
        var isEnchantment  = ct.includes('enchantment');
        var isInstant      = ct.includes('instant');
        var isSorcery      = ct.includes('sorcery');
        var isPlaneswalker = ct.includes('planeswalker');
        var isLand         = ct.includes('land');
        var isBattle       = ct.includes('battle');

        // Type counts — a card can appear in multiple bars
        if (isCreature)     typeCounts['Creature']     += qty;
        if (isArtifact)     typeCounts['Artifact']     += qty;
        if (isEnchantment)  typeCounts['Enchantment']  += qty;
        if (isInstant)      typeCounts['Instant']      += qty;
        if (isSorcery)      typeCounts['Sorcery']      += qty;
        if (isPlaneswalker) typeCounts['Planeswalker'] += qty;
        if (isLand)         typeCounts['Land']         += qty;
        if (!isCreature && !isArtifact && !isEnchantment && !isInstant &&
            !isSorcery && !isPlaneswalker && !isLand) {
            typeCounts['Other'] += qty;
        }

        // Mana curve: lands excluded
        if (isLand) return;

        var mv = getManaValue(cost);
        if (!manaCurve[mv]) manaCurve[mv] = { permanents: 0, spells: 0 };

        // Classify as permanent if any permanent supertype present
        var isPermanent = isCreature || isArtifact || isEnchantment || isPlaneswalker || isBattle;
        if (isPermanent) {
            manaCurve[mv].permanents += qty;
        } else {
            manaCurve[mv].spells += qty;
        }
    });

    if (manaCurveCanvas) _renderManaCurveChart(manaCurveCanvas, manaCurve);
    if (typeCanvas)      _renderTypeBreakdownChart(typeCanvas, typeCounts);
}

function _setupCanvas(canvas) {
    var wrap = canvas.parentElement; // .deck-chart-canvas-wrap
    var w = wrap.offsetWidth;
    var h = wrap.offsetHeight;
    if (w <= 0 || h <= 0) return null;
    var dpr = window.devicePixelRatio || 1;
    canvas.width  = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width  = w + 'px';
    canvas.style.height = h + 'px';
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return { ctx: ctx, w: w, h: h };
}

function _barLabel(ctx, count, cx, segTop, segH) {
    // Draw count label on or above a bar segment
    if (count === 0) return;
    ctx.textAlign = 'center';
    if (segH >= 16) {
        ctx.fillStyle = '#111';
        ctx.font = 'bold 10px sans-serif';
        ctx.fillText(count, cx, segTop + segH / 2 + 4);
    } else if (segH > 0) {
        ctx.fillStyle = '#333';
        ctx.font = 'bold 9px sans-serif';
        ctx.fillText(count, cx, segTop - 2);
    }
}

function _renderManaCurveChart(canvas, manaCurve) {
    var setup = _setupCanvas(canvas);
    if (!setup) return;
    var ctx = setup.ctx, w = setup.w, h = setup.h;

    var mvKeys = Object.keys(manaCurve).map(Number).sort(function(a, b) { return a - b; });
    if (!mvKeys.length) return;

    var maxMv = mvKeys[mvKeys.length - 1];
    var allMVs = [];
    for (var i = 0; i <= maxMv; i++) allMVs.push(i);

    var rawMax = 0;
    allMVs.forEach(function(mv) {
        var d = manaCurve[mv] || { permanents: 0, spells: 0 };
        var t = d.permanents + d.spells;
        if (t > rawMax) rawMax = t;
    });
    if (rawMax === 0) return;

    var gridStep = 10;
    var yMax = Math.ceil(rawMax / gridStep) * gridStep || gridStep;

    var ML = 26, MR = 8, MT = 12, MB = 52;
    var cW = w - ML - MR;
    var cH = h - MT - MB;
    var bot = MT + cH;
    var barW = cW / allMVs.length;
    var pad  = Math.max(barW * 0.13, 2);

    var PERM_COLOR  = '#f59e0b'; // amber  – permanents (bottom)
    var SPELL_COLOR = '#818cf8'; // indigo – spells (top)

    ctx.clearRect(0, 0, w, h);

    // Grid lines + y-axis labels (drawn first, behind bars)
    for (var v = gridStep; v <= yMax; v += gridStep) {
        var gy = bot - (v / yMax) * cH;
        ctx.strokeStyle = 'rgba(0,0,0,0.08)';
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(ML, gy);
        ctx.lineTo(ML + cW, gy);
        ctx.stroke();
        ctx.fillStyle = '#aaa';
        ctx.font = '9px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(v, ML - 3, gy + 3);
    }

    // Y-axis line + baseline
    ctx.strokeStyle = 'rgba(0,0,0,0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(ML, MT);
    ctx.lineTo(ML, bot);
    ctx.moveTo(ML, bot);
    ctx.lineTo(ML + cW, bot);
    ctx.stroke();

    // Bars
    allMVs.forEach(function(mv, idx) {
        var d      = manaCurve[mv] || { permanents: 0, spells: 0 };
        var bx     = ML + idx * barW + pad;
        var bw     = barW - 2 * pad;
        var permH  = (d.permanents / yMax) * cH;
        var spellH = (d.spells     / yMax) * cH;

        // Permanents: bottom segment
        if (permH > 0) {
            ctx.fillStyle = PERM_COLOR;
            ctx.fillRect(bx, bot - permH, bw, permH);
        }
        // Spells: top segment (stacked above permanents)
        if (spellH > 0) {
            ctx.fillStyle = SPELL_COLOR;
            ctx.fillRect(bx, bot - permH - spellH, bw, spellH);
        }

        var cx = bx + bw / 2;
        _barLabel(ctx, d.permanents, cx, bot - permH,               permH);
        _barLabel(ctx, d.spells,     cx, bot - permH - spellH, spellH);

        // X-axis MV label
        ctx.fillStyle = '#444';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(mv, ML + (idx + 0.5) * barW, bot + 14);
    });

    // Legend
    var legY = bot + 30;
    var legX = w / 2 - 88;

    ctx.fillStyle = PERM_COLOR;
    ctx.fillRect(legX, legY, 12, 12);
    ctx.fillStyle = '#444';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Permanents', legX + 16, legY + 10);

    ctx.fillStyle = SPELL_COLOR;
    ctx.fillRect(legX + 98, legY, 12, 12);
    ctx.fillStyle = '#444';
    ctx.fillText('Spells', legX + 114, legY + 10);
}

function _renderTypeBreakdownChart(canvas, typeCounts) {
    var setup = _setupCanvas(canvas);
    if (!setup) return;
    var ctx = setup.ctx, w = setup.w, h = setup.h;

    var ALL_TYPES  = ['Creature', 'Artifact', 'Enchantment', 'Instant', 'Sorcery', 'Planeswalker', 'Land', 'Other'];
    var ALL_COLORS = ['#ef4444',  '#8b5cf6',  '#10b981',     '#3b82f6', '#f97316', '#ec4899',      '#6b7280', '#d97706'];

    // Only draw bars for types that have at least one card
    var bars = [];
    for (var i = 0; i < ALL_TYPES.length; i++) {
        if (typeCounts[ALL_TYPES[i]] > 0) {
            bars.push({ type: ALL_TYPES[i], count: typeCounts[ALL_TYPES[i]], color: ALL_COLORS[i] });
        }
    }
    if (!bars.length) return;

    var rawMax = 0;
    bars.forEach(function(b) { if (b.count > rawMax) rawMax = b.count; });

    var gridStep = 10;
    var yMax = Math.ceil(rawMax / gridStep) * gridStep || gridStep;

    // Full labels unless >= 7 non-zero bars, then abbreviate Creature/Enchantment/Planeswalker
    var ABBREV = { 'Creature': 'Creat.', 'Enchantment': 'Ench.', 'Planeswalker': 'PW' };
    var useAbbrev = bars.length >= 7;

    var ML = 26, MR = 8, MT = 12, MB = 34;
    var cW = w - ML - MR;
    var cH = h - MT - MB;
    var bot = MT + cH;
    var barW = cW / bars.length;
    var pad  = Math.max(barW * 0.13, 2);

    ctx.clearRect(0, 0, w, h);

    // Grid lines + y-axis labels (drawn first, behind bars)
    for (var v = gridStep; v <= yMax; v += gridStep) {
        var gy = bot - (v / yMax) * cH;
        ctx.strokeStyle = 'rgba(0,0,0,0.08)';
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(ML, gy);
        ctx.lineTo(ML + cW, gy);
        ctx.stroke();
        ctx.fillStyle = '#aaa';
        ctx.font = '9px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(v, ML - 3, gy + 3);
    }

    // Y-axis line + baseline
    ctx.strokeStyle = 'rgba(0,0,0,0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(ML, MT);
    ctx.lineTo(ML, bot);
    ctx.moveTo(ML, bot);
    ctx.lineTo(ML + cW, bot);
    ctx.stroke();

    // Bars + labels
    bars.forEach(function(bar, idx) {
        var bx   = ML + idx * barW + pad;
        var bw   = barW - 2 * pad;
        var barH = (bar.count / yMax) * cH;

        ctx.fillStyle = bar.color;
        ctx.fillRect(bx, bot - barH, bw, barH);
        _barLabel(ctx, bar.count, bx + bw / 2, bot - barH, barH);

        var label = useAbbrev ? (ABBREV[bar.type] || bar.type) : bar.type;
        ctx.fillStyle = '#555';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(label, ML + (idx + 0.5) * barW, bot + 14);
    });

    // Footnote
    ctx.fillStyle = '#bbb';
    ctx.font = '9px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Cards may count in multiple bars', w / 2, h - 4);
}
