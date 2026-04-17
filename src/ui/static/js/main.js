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
    const legitimacyFilterSelect = document.getElementById('legitimacy-filter-select');
    const changedFilterSelect = document.getElementById('changed-filter-select');
    if (sortSelect && groupSelect) {
        sortSelect.addEventListener('change', applyCardControls);
        groupSelect.addEventListener('change', applyCardControls);
        if (mvOpSelect) mvOpSelect.addEventListener('change', applyCardControls);
        if (mvValueInput) mvValueInput.addEventListener('input', applyCardControls);
        if (typeFilterSelect) typeFilterSelect.addEventListener('change', applyCardControls);
        if (legitimacyFilterSelect) legitimacyFilterSelect.addEventListener('change', applyCardControls);
        if (changedFilterSelect) changedFilterSelect.addEventListener('change', applyCardControls);
        // Apply defaults immediately on page load
        applyCardControls();
    }

    var resetControlsBtn = document.getElementById('reset-controls-btn');
    if (resetControlsBtn) {
        resetControlsBtn.addEventListener('click', function () {
            if (sortSelect)             sortSelect.value             = 'mana';
            if (groupSelect)            groupSelect.value            = 'type';
            if (mvOpSelect)             mvOpSelect.value             = 'any';
            if (mvValueInput)           mvValueInput.value           = '';
            if (typeFilterSelect)       typeFilterSelect.value       = 'any';
            if (legitimacyFilterSelect) legitimacyFilterSelect.value = 'any';
            if (changedFilterSelect)    changedFilterSelect.value    = 'any';
            applyCardControls();
        });
    }

    // Render deck charts if present (deferred so layout is settled)
    if (document.getElementById('manaCurveChart') || document.getElementById('typeBreakdownChart')) {
        requestAnimationFrame(function() { renderDeckCharts(); });
    }

    // Compute mana production breakdown and wire +/− buttons
    if (document.getElementById('mbc-w')) {
        requestAnimationFrame(function() {
            computeManaBreakdown();
            document.querySelectorAll('.mana-add-basic-btn').forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    _doBasicAction(btn.dataset.color, 'add-basic', btn);
                });
            });
            document.querySelectorAll('.mana-remove-basic-btn').forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    _doBasicAction(btn.dataset.color, 'remove-basic', btn);
                });
            });
        });
    }

    // Floating scroll navigation buttons
    const scrollTopBtn = document.getElementById('scroll-top-btn');
    const scrollPrevGroupBtn = document.getElementById('scroll-prev-group-btn');
    const scrollNextGroupBtn = document.getElementById('scroll-next-group-btn');
    const scrollBottomBtn = document.getElementById('scroll-bottom-btn');

    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
    if (scrollPrevGroupBtn) {
        scrollPrevGroupBtn.addEventListener('click', function() {
            const headers = Array.from(document.querySelectorAll('.card-group-header'));
            if (!headers.length) return;
            const prev = headers.slice().reverse().find(function(h) {
                return h.getBoundingClientRect().top < -10;
            });
            if (prev) {
                prev.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
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
        // Scope to #cards-tab-main so token gallery items in the Tokens tab
        // are never captured and moved into the cards list by applyCardControls.
        var cardsList = document.getElementById('cards-tab-main') || document;
        _canonicalCardItems = Array.from(cardsList.querySelectorAll('.card-gallery-item'));
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
        case 'noncreature':        return !ct.includes('creature');
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
    const legitimacyEl = document.getElementById('legitimacy-filter-select');
    const changedEl = document.getElementById('changed-filter-select');
    const mvOp = mvOpEl ? mvOpEl.value : 'any';
    const mvValue = mvValEl ? mvValEl.value : '';
    const typeFilter = typeFilterEl ? typeFilterEl.value : 'any';
    const legitimacyFilter = legitimacyEl ? legitimacyEl.value : 'any';
    const changedFilter = changedEl ? changedEl.value : 'any';

    // Always work from the canonical snapshot, not whatever is currently in the DOM
    // (tag grouping leaves clones in the DOM that would inflate counts otherwise)
    const allItems = [...getCanonicalItems()];
    if (!allItems.length) return;

    // Apply filters (commander stat items are always excluded from gallery display)
    const filteredItems = allItems.filter(function(item) {
        if (item.dataset.commanderStat) return false;
        if (!matchesManaFilter(item, mvOp, mvValue)) return false;
        if (!matchesTypeFilter(item, typeFilter)) return false;
        if (legitimacyFilter === 'real'   && !(parseInt(item.dataset.real, 10) === 1)) return false;
        if (legitimacyFilter === 'custom' &&   parseInt(item.dataset.real, 10) === 1)  return false;
        if (changedFilter === 'yes' && item.dataset.staged !== 'true')  return false;
        if (changedFilter === 'no'  && item.dataset.staged === 'true')  return false;
        return true;
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

// Hit regions for chart hover tooltips (updated on each render)
var _manaCurveHitRegions = [];
var _typeBreakdownHitRegions = [];
var _chartHoverSetup = false;

function renderDeckCharts() {
    var manaCurveCanvas = document.getElementById('manaCurveChart');
    var typeCanvas = document.getElementById('typeBreakdownChart');
    if (!manaCurveCanvas && !typeCanvas) return;

    // Use canonical items so we always see the full deck regardless of filters
    var items = getCanonicalItems();

    var manaCurve = {}; // { mv: { permanents: N, spells: N } }
    var manaCurveNames = {}; // { mv: { permanents: [], spells: [] } }
    var typeCounts = {
        'Creature': 0, 'Artifact': 0, 'Enchantment': 0,
        'Instant': 0, 'Sorcery': 0, 'Planeswalker': 0,
        'Land': 0, 'Other': 0
    };
    var typeNames = {
        'Creature': [], 'Artifact': [], 'Enchantment': [],
        'Instant': [], 'Sorcery': [], 'Planeswalker': [],
        'Land': [], 'Other': []
    };

    var totalCardCount = 0;
    var nonLandCount   = 0;
    var totalMV        = 0;

    items.forEach(function(item) {
        var cost    = item.dataset.cost     || '';
        var cardtype = item.dataset.cardtype || '';
        var qty     = parseInt(item.dataset.quantity, 10) || 1;
        var ct      = cardtype.toLowerCase();
        var cardName = item.dataset.name || '';

        var isCreature     = ct.includes('creature');
        var isArtifact     = ct.includes('artifact');
        var isEnchantment  = ct.includes('enchantment');
        var isInstant      = ct.includes('instant');
        var isSorcery      = ct.includes('sorcery');
        var isPlaneswalker = ct.includes('planeswalker');
        var isLand         = ct.includes('land');
        var isBattle       = ct.includes('battle');

        totalCardCount += qty;

        // Type counts — a card can appear in multiple bars
        if (isCreature)     { typeCounts['Creature']     += qty; if (cardName) typeNames['Creature'].push(cardName); }
        if (isArtifact)     { typeCounts['Artifact']     += qty; if (cardName) typeNames['Artifact'].push(cardName); }
        if (isEnchantment)  { typeCounts['Enchantment']  += qty; if (cardName) typeNames['Enchantment'].push(cardName); }
        if (isInstant)      { typeCounts['Instant']      += qty; if (cardName) typeNames['Instant'].push(cardName); }
        if (isSorcery)      { typeCounts['Sorcery']      += qty; if (cardName) typeNames['Sorcery'].push(cardName); }
        if (isPlaneswalker) { typeCounts['Planeswalker'] += qty; if (cardName) typeNames['Planeswalker'].push(cardName); }
        if (isLand)         { typeCounts['Land']         += qty; if (cardName) typeNames['Land'].push(cardName); }
        if (!isCreature && !isArtifact && !isEnchantment && !isInstant &&
            !isSorcery && !isPlaneswalker && !isLand) {
            typeCounts['Other'] += qty;
            if (cardName) typeNames['Other'].push(cardName);
        }

        // Mana curve: lands excluded
        if (isLand) return;

        var mv = getManaValue(cost);
        nonLandCount += qty;
        totalMV      += mv * qty;

        if (!manaCurve[mv]) manaCurve[mv] = { permanents: 0, spells: 0 };
        if (!manaCurveNames[mv]) manaCurveNames[mv] = { permanents: [], spells: [] };

        // Classify as permanent if any permanent supertype present
        var isPermanent = isCreature || isArtifact || isEnchantment || isPlaneswalker || isBattle;
        if (isPermanent) {
            manaCurve[mv].permanents += qty;
            if (cardName) manaCurveNames[mv].permanents.push(cardName);
        } else {
            manaCurve[mv].spells += qty;
            if (cardName) manaCurveNames[mv].spells.push(cardName);
        }
    });

    var mvStats = {
        totalMV:    totalMV,
        avgAll:     totalCardCount > 0 ? totalMV / totalCardCount : 0,
        avgNonLand: nonLandCount   > 0 ? totalMV / nonLandCount   : 0
    };

    if (manaCurveCanvas) _renderManaCurveChart(manaCurveCanvas, manaCurve, mvStats, manaCurveNames);
    if (typeCanvas)      _renderTypeBreakdownChart(typeCanvas, typeCounts, typeNames);

    _ensureChartHoverSetup(manaCurveCanvas, typeCanvas);
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

function _renderManaCurveChart(canvas, manaCurve, mvStats, manaCurveNames) {
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
    _manaCurveHitRegions = [];
    allMVs.forEach(function(mv, idx) {
        var d      = manaCurve[mv] || { permanents: 0, spells: 0 };
        var names  = manaCurveNames ? (manaCurveNames[mv] || { permanents: [], spells: [] }) : { permanents: [], spells: [] };
        var bx     = ML + idx * barW + pad;
        var bw     = barW - 2 * pad;
        var permH  = (d.permanents / yMax) * cH;
        var spellH = (d.spells     / yMax) * cH;

        // Permanents: bottom segment
        if (permH > 0) {
            ctx.fillStyle = PERM_COLOR;
            ctx.fillRect(bx, bot - permH, bw, permH);
            _manaCurveHitRegions.push({ x: bx, y: bot - permH, w: bw, h: permH,
                label: 'MV ' + mv + ' \u2014 Permanents', names: names.permanents.slice().sort() });
        }
        // Spells: top segment (stacked above permanents)
        if (spellH > 0) {
            ctx.fillStyle = SPELL_COLOR;
            ctx.fillRect(bx, bot - permH - spellH, bw, spellH);
            _manaCurveHitRegions.push({ x: bx, y: bot - permH - spellH, w: bw, h: spellH,
                label: 'MV ' + mv + ' \u2014 Spells', names: names.spells.slice().sort() });
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

    // Legend (left-aligned) + stats (right-aligned) on the same row
    var legY = bot + 30;
    var legX = ML;

    ctx.fillStyle = PERM_COLOR;
    ctx.fillRect(legX, legY, 12, 12);
    ctx.fillStyle = '#444';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Permanents', legX + 16, legY + 10);

    ctx.fillStyle = SPELL_COLOR;
    ctx.fillRect(legX + 98, legY, 12, 12);
    ctx.fillStyle = '#444';
    ctx.fillText('Spells', legX + 114, legY + 10);

    // MV stats right-aligned on the same row as the legend
    if (mvStats) {
        var avgAllStr     = mvStats.avgAll.toFixed(2);
        var avgNonLandStr = mvStats.avgNonLand.toFixed(2);
        ctx.fillStyle = '#666';
        ctx.font = '13px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(
            'Mean: ' + avgAllStr + ' (' + avgNonLandStr + ' excl. lands)   Total: ' + mvStats.totalMV,
            w - MR, legY + 10
        );
    }
}

function _renderTypeBreakdownChart(canvas, typeCounts, typeNames) {
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
    _typeBreakdownHitRegions = [];
    bars.forEach(function(bar, idx) {
        var bx   = ML + idx * barW + pad;
        var bw   = barW - 2 * pad;
        var barH = (bar.count / yMax) * cH;

        ctx.fillStyle = bar.color;
        ctx.fillRect(bx, bot - barH, bw, barH);
        _barLabel(ctx, bar.count, bx + bw / 2, bot - barH, barH);

        var names = typeNames ? (typeNames[bar.type] || []) : [];
        _typeBreakdownHitRegions.push({ x: bx, y: bot - barH, w: bw, h: barH,
            label: bar.type, names: names.slice().sort() });

        var label = useAbbrev ? (ABBREV[bar.type] || bar.type) : bar.type;
        ctx.fillStyle = '#555';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(label, ML + (idx + 0.5) * barW, bot + 14);
    });

    // Footnote
    ctx.fillStyle = '#bbb';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Cards may count in multiple bars', w / 2, h - 4);
}

// ─── Chart Hover Tooltips ─────────────────────────────────────────────────────

function _ensureChartHoverSetup(manaCurveCanvas, typeCanvas) {
    if (_chartHoverSetup) return;
    _chartHoverSetup = true;

    function onMove(hitRegionsRef) {
        return function(e) {
            var rect = e.currentTarget.getBoundingClientRect();
            var mx = e.clientX - rect.left;
            var my = e.clientY - rect.top;
            var hit = null;
            for (var i = 0; i < hitRegionsRef().length; i++) {
                var r = hitRegionsRef()[i];
                if (mx >= r.x && mx <= r.x + r.w && my >= r.y && my <= r.y + r.h) {
                    hit = r;
                    break;
                }
            }
            if (hit && hit.names.length > 0) {
                _showChartTooltip(e.clientX, e.clientY, hit.label, hit.names);
            } else {
                _hideChartTooltip();
            }
        };
    }

    if (manaCurveCanvas) {
        manaCurveCanvas.addEventListener('mousemove', onMove(function() { return _manaCurveHitRegions; }));
        manaCurveCanvas.addEventListener('mouseleave', _hideChartTooltip);
    }
    if (typeCanvas) {
        typeCanvas.addEventListener('mousemove', onMove(function() { return _typeBreakdownHitRegions; }));
        typeCanvas.addEventListener('mouseleave', _hideChartTooltip);
    }
}

function _showChartTooltip(clientX, clientY, label, names) {
    var tip = document.getElementById('chart-hover-tooltip');
    if (!tip) {
        tip = document.createElement('div');
        tip.id = 'chart-hover-tooltip';
        document.body.appendChild(tip);
    }
    var html = '<div class="chart-tip-label">' + label + '</div>';
    for (var i = 0; i < names.length; i++) {
        html += '<div class="chart-tip-name">' + names[i] + '</div>';
    }
    tip.innerHTML = html;
    tip.style.display = 'block';
    var x = clientX + 14;
    var y = clientY + 14;
    // Keep within viewport
    tip.style.left = '-9999px';  // measure off-screen first
    tip.style.top  = '-9999px';
    var tipW = tip.offsetWidth  || 200;
    var tipH = tip.offsetHeight || 100;
    if (x + tipW > window.innerWidth)  x = clientX - tipW - 8;
    if (y + tipH > window.innerHeight) y = clientY - tipH - 8;
    tip.style.left = x + 'px';
    tip.style.top  = y + 'px';
}

function _hideChartTooltip() {
    var tip = document.getElementById('chart-hover-tooltip');
    if (tip) tip.style.display = 'none';
}

// ─── Mana Production Breakdown ───────────────────────────────────────────────

function getPipCountsFromCost(cost) {
    var counts = { w: 0, u: 0, b: 0, r: 0, g: 0, c: 0 };
    if (!cost) return counts;
    var matches = cost.match(/\{([^}]+)\}/g) || [];
    for (var i = 0; i < matches.length; i++) {
        var inner = matches[i].slice(1, -1).toLowerCase();
        // Skip generic numeric, variable, snow, energy, tap/untap symbols
        if (/^\d+$/.test(inner)) continue;
        if (inner === 'x' || inner === 'y' || inner === 'z') continue;
        if (inner === 's' || inner === 'e' || inner === 't' || inner === 'q') continue;
        if (inner.includes('/')) {
            // Hybrid / phyrexian / colorless-hybrid: count each color component
            var parts = inner.split('/');
            for (var j = 0; j < parts.length; j++) {
                var p = parts[j];
                if (p === 'w') counts.w += 1;
                else if (p === 'u') counts.u += 1;
                else if (p === 'b') counts.b += 1;
                else if (p === 'r') counts.r += 1;
                else if (p === 'g') counts.g += 1;
                else if (p === 'c') counts.c += 1;
                // numeric '2' in {2/W} and phyrexian 'p' are ignored
            }
        } else {
            if (inner === 'w') counts.w += 1;
            else if (inner === 'u') counts.u += 1;
            else if (inner === 'b') counts.b += 1;
            else if (inner === 'r') counts.r += 1;
            else if (inner === 'g') counts.g += 1;
            else if (inner === 'c') counts.c += 1;
        }
    }
    return counts;
}

var BASIC_SUBTYPES = { w: 'plains', u: 'island', b: 'swamp', r: 'mountain', g: 'forest', c: 'wastes' };

function computeManaBreakdown() {
    if (!document.getElementById('mbc-w')) return;

    var items = getCanonicalItems();
    var COLORS = ['w', 'u', 'b', 'r', 'g', 'c'];

    var cardCounts  = { w: 0, u: 0, b: 0, r: 0, g: 0, c: 0 };
    var totalNonLand = 0;
    var pipCounts   = { w: 0, u: 0, b: 0, r: 0, g: 0, c: 0 };
    var totalPips   = 0;
    var basicCounts = { w: 0, u: 0, b: 0, r: 0, g: 0, c: 0 };

    items.forEach(function(item) {
        var cost     = item.dataset.cost    || '';
        var cardtype = (item.dataset.cardtype || '').toLowerCase();
        var subtype  = (item.dataset.subtype  || '').toLowerCase();
        var isBasic  = !!(item.dataset.basic  && item.dataset.basic !== '0' && item.dataset.basic !== '');
        var qty      = parseInt(item.dataset.quantity || '1', 10) || 1;
        var isLand   = cardtype.includes('land');

        if (!isLand) {
            var cardColors = getColorsFromCost(cost);
            if (cardColors.length === 0) {
                cardCounts.c += qty;
            } else {
                for (var i = 0; i < cardColors.length; i++) {
                    cardCounts[cardColors[i].toLowerCase()] += qty;
                }
            }
            totalNonLand += qty;
        }

        var pips = getPipCountsFromCost(cost);
        for (var k = 0; k < COLORS.length; k++) {
            var added = pips[COLORS[k]] * qty;
            pipCounts[COLORS[k]] += added;
            totalPips += added;
        }

        // Basic land: flagged via data-basic (front.basic=1) or subtype matches a basic type
        if (isBasic && isLand) {
            for (var b = 0; b < COLORS.length; b++) {
                if (subtype.includes(BASIC_SUBTYPES[COLORS[b]])) {
                    basicCounts[COLORS[b]] += qty;
                }
            }
        }
    });

    COLORS.forEach(function(color) {
        var cardsEl  = document.getElementById('mb-cards-'  + color);
        var pipsEl   = document.getElementById('mb-pips-'   + color);
        var basicsEl = document.getElementById('mb-basics-' + color);
        var colorEl  = document.getElementById('mbc-' + color);
        if (!colorEl) return;

        var cardPct = totalNonLand > 0 ? (cardCounts[color] / totalNonLand * 100) : 0;
        var pipPct  = totalPips    > 0 ? (pipCounts[color]  / totalPips    * 100) : 0;

        if (cardsEl)  cardsEl.textContent  = cardPct.toFixed(0) + '%';
        if (pipsEl)   pipsEl.textContent   = pipPct.toFixed(0)  + '%';
        if (basicsEl) basicsEl.textContent = basicCounts[color];

        if (cardCounts[color] === 0 && basicCounts[color] === 0) {
            colorEl.classList.add('mana-color-absent');
        } else {
            colorEl.classList.remove('mana-color-absent');
        }
    });

}

function _updateBasicCard(color, newQty, isAdd) {
    var basicSubtype = BASIC_SUBTYPES[color];
    if (!_canonicalCardItems) return;

    var matchingItem = null;
    for (var i = 0; i < _canonicalCardItems.length; i++) {
        var item = _canonicalCardItems[i];
        if (item.dataset.basic && item.dataset.basic !== '0' && item.dataset.basic !== '' &&
            (item.dataset.subtype || '').toLowerCase().includes(basicSubtype)) {
            matchingItem = item;
            break;
        }
    }

    if (!matchingItem) {
        // Card not yet in the DOM — reload to show the newly-added basic land
        if (isAdd) location.reload();
        return;
    }

    if (newQty <= 0) {
        // Remove from canonical list and DOM, then rebuild gallery grouping
        _canonicalCardItems = _canonicalCardItems.filter(function(i) { return i !== matchingItem; });
        matchingItem.remove();
        applyCardControls();
        return;
    }

    // Update cached dataset so applyCardControls counts correctly
    matchingItem.dataset.quantity = newQty;

    // Update the yellow quantity badge
    var container = matchingItem.querySelector('.card-image-container') ||
                    matchingItem.querySelector('.card-image-placeholder');
    if (container) {
        var badge = container.querySelector('.quantity-badge');
        if (newQty > 1) {
            if (badge) {
                badge.textContent = 'x' + newQty;
            } else {
                var newBadge = document.createElement('div');
                newBadge.className = 'quantity-badge';
                newBadge.textContent = 'x' + newQty;
                container.appendChild(newBadge);
            }
        } else {
            if (badge) badge.remove();
        }
    }

    // Refresh the "Cards (N)" header count
    applyCardControls();
}

function _doBasicAction(color, action, btn) {
    var breakdownEl = document.querySelector('.mana-breakdown');
    var deckName = breakdownEl ? breakdownEl.dataset.deckName : '';
    if (!deckName || !color) return;

    btn.disabled = true;
    fetch('/deck/' + encodeURIComponent(deckName) + '/' + action + '/' + color, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.error) { btn.disabled = false; return; }

        var basicsEl = document.getElementById('mb-basics-' + color);
        if (basicsEl) basicsEl.textContent = data.quantity;

        var countEl = document.querySelector('.deck-card-count');
        if (countEl && data.total_cards !== undefined) {
            countEl.textContent = countEl.textContent.replace(/^\d+/, data.total_cards);
        }

        _updateBasicCard(color, data.quantity, action === 'add-basic');

        var colorEl = document.getElementById('mbc-' + color);
        if (colorEl && data.quantity > 0) colorEl.classList.remove('mana-color-absent');

        btn.disabled = false;
    })
    .catch(function() { btn.disabled = false; });
}

// ─── Deck Tab System + Inline Card Editor (Phase 1 & 2) ──────────────────────

(function () {
    'use strict';

    // ── State ──────────────────────────────────────────────────────────────────
    var _deckName        = '';
    var _currentCardName = null;
    var _isNewCard       = false;
    var _editorOpenedAt  = 0;
    var _savedScrollY    = 0;
    var _originalJson    = '';
    var _editorIsDirty   = false;
    var _editorMode      = 'form';
    var _cmEditor        = null;
    var _stagedCount     = 0;
    var _currentFace     = 'front';  // 'front' | 'back'
    var _faceCache       = { front: {}, back: {} };
    var _serverData      = null;
    var _currentTags     = [];   // tags on the current card
    var _deckTags        = [];   // all tags in the deck
    var _subspellActive  = false;
    var _multiSectionMode = null;   // null | 'saga' | 'class' | 'planeswalker'
    var _commanderNames  = [];      // card names currently set as commanders

    // ── Real Card Dialog state ─────────────────────────────────────────────────
    var _rcdMode           = 'add';  // 'add' | 'edit'
    var _rcdSelectedCard   = null;   // card object from Scryfall search
    var _rcdSelectedPrinting = null; // printing object from Scryfall
    var _rcdSearchTimer    = null;
    var _rcdCardBeingEdited = null;  // card name when mode === 'edit'
    var _ohPool        = [];        // shuffled deck pool for Opening Hand
    var _ohPosition    = 0;         // index of next card to deal from pool
    var _ohDrawnCount  = 0;         // how many extra draws have been made
    var _ohInitialized = false;     // whether the opening hand has been seeded

    // ── Tiny helpers ──────────────────────────────────────────────────────────
    function $id(id) { return document.getElementById(id); }

    function setVal(id, val) {
        var el = $id(id);
        if (el) el.value = (val !== undefined && val !== null) ? String(val) : '';
    }

    function setCheck(id, checked) {
        var el = $id(id);
        if (el) el.checked = !!checked;
    }

    // ── Subspell helpers ──────────────────────────────────────────────────────
    var _SS_FIELDS = ['name', 'mana', 'cardtype', 'subtype', 'rules'];

    function _setSubspellActive(active) {
        _subspellActive = active;
        var section = $id('ef-subspell-section');
        var addRow  = $id('ef-add-subspell-row');
        if (section) section.style.display = active ? '' : 'none';
        if (addRow)  addRow.style.display  = active ? 'none' : '';
    }

    function _captureSubspell() {
        if (!_subspellActive) return null;
        var ss = {};
        _SS_FIELDS.forEach(function (k) {
            var el = $id('ef-ss-' + k);
            if (el && el.value.trim()) ss[k] = el.value.trim();
        });
        return Object.keys(ss).length > 0 ? ss : null;
    }

    function _populateSubspell(ss) {
        _setSubspellActive(!!ss);
        _SS_FIELDS.forEach(function (k) {
            setVal('ef-ss-' + k, (ss && ss[k]) || '');
        });
    }

    // ── Multi-section Rules helpers ───────────────────────────────────────────
    var _ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI'];

    function _getMultiSectionType() {
        var ct  = ($id('ef-cardtype') || {}).value || '';
        var st  = ($id('ef-subtype')  || {}).value || '';
        var ctL = ct.toLowerCase();
        var stL = st.toLowerCase();
        if (ctL.includes('planeswalker')) return 'planeswalker';
        if (ctL.includes('enchantment') && stL.includes('saga')) return 'saga';
        if (stL.includes('class')) return 'class';
        return null;
    }

    function _activateMultiSection(mode, sections) {
        _multiSectionMode = mode;
        var singleDiv = $id('ef-rules-single');
        var multiDiv  = $id('ef-rules-multi');
        var label     = $id('ef-rules-multi-label');
        if (!singleDiv || !multiDiv) return;
        if (mode === null) {
            singleDiv.style.display = '';
            multiDiv.style.display  = 'none';
        } else {
            singleDiv.style.display = 'none';
            multiDiv.style.display  = '';
            if (label) {
                label.textContent = mode === 'saga'         ? 'Chapters'          :
                                    mode === 'class'        ? 'Class Levels'      :
                                    /* planeswalker */        'Loyalty Abilities';
            }
            _renderSections(mode, sections && sections.length ? sections : [{ text: '', loyalty: '' }]);
        }
    }

    function _renderSections(mode, sections) {
        var container = $id('ef-sections-container');
        if (!container) return;
        container.innerHTML = '';
        sections.forEach(function (sec, idx) {
            container.appendChild(_buildSectionRow(idx, mode, sec.text || '', sec.loyalty || ''));
        });
    }

    function _buildSectionRow(idx, mode, text, loyalty) {
        var row = document.createElement('div');
        row.className = 'ef-section-row';
        row.dataset.index = idx;

        if (mode === 'saga') {
            var lbl = document.createElement('span');
            lbl.className = 'ef-section-label ef-section-label--saga';
            lbl.textContent = _ROMAN[idx] || String(idx + 1);
            row.appendChild(lbl);
        } else if (mode === 'class') {
            var lbl = document.createElement('span');
            lbl.className = 'ef-section-label ef-section-label--class';
            lbl.textContent = 'Level\u00a0' + (idx + 1);
            row.appendChild(lbl);
        } else if (mode === 'planeswalker') {
            var loyInput = document.createElement('input');
            loyInput.type = 'text';
            loyInput.className = 'ef-input ef-loyalty-input';
            loyInput.placeholder = '+1';
            loyInput.value = loyalty;
            loyInput.addEventListener('input',  onFormChange);
            loyInput.addEventListener('change', onFormChange);
            row.appendChild(loyInput);
        }

        var ta = document.createElement('textarea');
        ta.className = 'ef-input ef-textarea ef-section-textarea';
        ta.rows = 2;
        ta.placeholder = 'Mana symbols: {w}{u}{b}{r}{g}{c}. Tap: {t}.';
        ta.value = text;
        ta.addEventListener('input',  onFormChange);
        ta.addEventListener('change', onFormChange);
        row.appendChild(ta);

        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-sm ef-section-remove-btn';
        removeBtn.title = 'Remove section';
        removeBtn.textContent = '−';
        row.appendChild(removeBtn);

        return row;
    }

    function _markSectionChange() {
        // Structural add/remove is always a meaningful change — don't rely on JSON comparison.
        if (!_currentCardName && !_isNewCard) return;
        _editorIsDirty = true;
        updateButtonStates();
    }

    function _addSection() {
        var container = $id('ef-sections-container');
        if (!container) return;
        if (container.querySelectorAll('.ef-section-row').length >= 6) return;
        var newRow = _buildSectionRow(
            container.querySelectorAll('.ef-section-row').length,
            _multiSectionMode, '', '');
        container.appendChild(newRow);
        _markSectionChange();
    }

    function _renumberSections() {
        var container = $id('ef-sections-container');
        if (!container) return;
        container.querySelectorAll('.ef-section-row').forEach(function (row, newIdx) {
            row.dataset.index = newIdx;
            var sagaLbl  = row.querySelector('.ef-section-label--saga');
            var classLbl = row.querySelector('.ef-section-label--class');
            if (sagaLbl)  sagaLbl.textContent  = _ROMAN[newIdx] || String(newIdx + 1);
            if (classLbl) classLbl.textContent  = 'Level\u00a0' + (newIdx + 1);
        });
    }

    function _captureSections() {
        var container = $id('ef-sections-container');
        if (!container) return [];
        var results = [];
        container.querySelectorAll('.ef-section-row').forEach(function (row) {
            var ta       = row.querySelector('.ef-section-textarea');
            var loyInput = row.querySelector('.ef-loyalty-input');
            results.push({
                text:    ta       ? ta.value       : '',
                loyalty: loyInput ? loyInput.value : ''
            });
        });
        return results;
    }

    function _onCardTypeChange() {
        var newMode = _getMultiSectionType();
        if (newMode === _multiSectionMode) return;

        if (newMode === null) {
            // Multi → Single: concatenate section texts
            var combined = _captureSections().map(function (s) { return s.text; }).filter(Boolean).join('\n');
            _activateMultiSection(null, []);
            setVal('ef-rules', combined);
        } else if (_multiSectionMode === null) {
            // Single → Multi: move existing rules text into first section
            var existing = ($id('ef-rules') || {}).value || '';
            _activateMultiSection(newMode, [{ text: existing, loyalty: '' }]);
        } else {
            // Multi → different multi (e.g. saga → planeswalker): keep texts
            var sections = _captureSections();
            _activateMultiSection(newMode, sections);
        }
        onFormChange();
    }

    // ── Face data helpers ─────────────────────────────────────────────────────
    var _FACE_STR_FIELDS  = ['name', 'mana', 'cardtype', 'subtype', 'rules', 'power', 'toughness', 'flavor', 'frame'];
    var _FACE_BOOL_FIELDS = ['legendary', 'basic', 'snow'];

    function buildFaceDict(faceData) {
        var f = faceData || {};
        var result = {};
        _FACE_STR_FIELDS.forEach(function (k)  { if (f[k]) result[k] = f[k]; });
        _FACE_BOOL_FIELDS.forEach(function (k) { if (f[k]) result[k] = 1; });
        for (var i = 1; i <= 6; i++) {
            if (f['rules'   + i]) result['rules'   + i] = f['rules'   + i];
            if (f['loyalty' + i]) result['loyalty' + i] = f['loyalty' + i];
        }
        return result;
    }

    function populateFaceForm(faceDict) {
        var f = faceDict || {};
        _FACE_STR_FIELDS.forEach(function (k)  { setVal('ef-' + k, f[k] || ''); });
        _FACE_BOOL_FIELDS.forEach(function (k) { setCheck('ef-' + k, f[k]); });
        // After fields are set, determine if multi-section mode is needed
        var mode = _getMultiSectionType();
        var hasMultiRules = false;
        for (var i = 1; i <= 6; i++) { if (f['rules' + i]) { hasMultiRules = true; break; } }
        if (mode !== null || hasMultiRules) {
            var sections = [];
            for (var i = 1; i <= 6; i++) {
                var text    = f['rules'   + i] || '';
                var loyalty = f['loyalty' + i] || '';
                if (text || loyalty) sections.push({ text: text, loyalty: loyalty });
            }
            _activateMultiSection(mode || 'saga', sections.length ? sections : [{ text: '', loyalty: '' }]);
        } else {
            _activateMultiSection(null, []);
        }
    }

    function captureCurrentFace() {
        var raw = {};
        _FACE_STR_FIELDS.forEach(function (k) {
            var el = $id('ef-' + k);
            if (el) raw[k] = el.value;
        });
        _FACE_BOOL_FIELDS.forEach(function (k) {
            var el = $id('ef-' + k);
            if (el) raw[k] = el.checked ? 1 : 0;
        });
        if (_multiSectionMode !== null) {
            raw.rules = '';   // suppress single rules field
            _captureSections().forEach(function (sec, idx) {
                if (sec.text)    raw['rules'   + (idx + 1)] = sec.text;
                if (sec.loyalty) raw['loyalty' + (idx + 1)] = sec.loyalty;
            });
        }
        return buildFaceDict(raw);
    }

    function updateFaceTabs() {
        document.querySelectorAll('.editor-face-tab').forEach(function (btn) {
            btn.classList.toggle('editor-face-tab--active', btn.dataset.face === _currentFace);
        });
    }

    function switchFace(face) {
        if (face === _currentFace) return;
        _faceCache[_currentFace] = captureCurrentFace();
        _currentFace = face;
        if (_editorMode === 'form') populateFaceForm(_faceCache[_currentFace]);
        updateFaceTabs();
        // Auto-select Transform when switching to Back if no DFC type is set yet
        if (face === 'back') {
            var dfcEl = $id('ef-dfc-type');
            if (dfcEl && !dfcEl.value) {
                dfcEl.value = 'transform';
            }
        }
        // Update preview to show the image for the selected face
        if (_serverData) {
            var faceImg = (face === 'front')
                ? (_serverData.image_base64 || null)
                : (_serverData.back_image_base64 || null);
            updatePreview(faceImg);
        }
        onFormChange();
    }

    // ── Tab Switching ─────────────────────────────────────────────────────────
    function switchTab(tabName, pushHash) {
        document.querySelectorAll('.deck-tab').forEach(function (btn) {
            btn.classList.toggle('deck-tab--active', btn.dataset.tab === tabName);
        });
        ['cards', 'tokens', 'assembly', 'opening-hand', 'forge-all'].forEach(function (key) {
            var pane = $id('tab-' + key);
            if (!pane) return;
            var show = (key === tabName);
            pane.style.display = show ? '' : 'none';
            pane.classList.toggle('tab-pane--active', show);
        });
        if (pushHash) history.replaceState(null, '', '#' + tabName);
        if (tabName === 'assembly') loadAssemblyLineData();
        if (tabName === 'opening-hand') _ohInitOnFirstSwitch();
    }

    function handleHash(hash) {
        if (!hash || hash === '#' || hash === '#cards') { switchTab('cards', false); return; }
        if (hash === '#tokens')   { switchTab('tokens', false);   return; }
        if (hash === '#assembly') { switchTab('assembly', false); return; }
        if (hash === '#opening-hand') { switchTab('opening-hand', false); return; }
        if (hash === '#forge-all')    { switchTab('forge-all', false);    return; }
        if (hash.startsWith('#edit/')) {
            var cardName = decodeURIComponent(hash.slice(6));
            switchTab('cards', false);
            openCardEditor(cardName);
            return;
        }
        if (hash === '#new-card') {
            switchTab('cards', false);
            openNewCardEditor();
            return;
        }
        switchTab('cards', false);
    }

    // ── Commander Button ──────────────────────────────────────────────────────
    function _updateCommanderBtn(cardName) {
        var btn = $id('set-commander-btn');
        if (!btn) return;
        var isCmd = _commanderNames.indexOf(cardName) !== -1;
        btn.textContent = isCmd ? '★ Unset as Commander' : '☆ Set As Commander';
        btn.classList.toggle('btn-set-commander--active', isCmd);
        btn.style.display = '';
    }

    // ── Open / Close Editor ───────────────────────────────────────────────────
    function openCardEditor(cardName) {
        // If this is a real card, open the real card editor dialog instead
        var _galEl = document.querySelector('.card-gallery-item[data-card-name="' + cardName.replace(/"/g, '\\"') + '"]');
        if (!_galEl) {
            _galEl = document.querySelector('#commander-stat-items [data-card-name="' + cardName.replace(/"/g, '\\"') + '"]');
        }
        if (_galEl && parseInt(_galEl.dataset.real, 10) === 1) {
            history.replaceState(null, '', '#cards');
            openRealCardEditorForCard(cardName);
            return;
        }

        _savedScrollY    = window.scrollY;
        _currentCardName = cardName;
        _isNewCard       = false;
        _editorIsDirty   = false;
        _editorOpenedAt  = Date.now();
        _currentFace     = 'front';
        _faceCache       = { front: {}, back: {} };
        _serverData      = null;

        $id('editor-card-title').textContent = cardName;
        _updateCommanderBtn(cardName);
        var delBtn = $id('delete-card-btn');
        if (delBtn) delBtn.style.display = '';
        $id('cards-tab-main').style.display  = 'none';
        $id('card-editor-panel').style.display = '';

        // Scroll to editor (needed when opening from commander images above the tab area)
        setTimeout(function () {
            var panel = $id('card-editor-panel');
            if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 30);

        switchEditorMode('form', /* silent */ true);
        history.replaceState(null, '', '#edit/' + encodeURIComponent(cardName));

        // Use query param so card names containing "/" (DFCs) aren't misrouted
        fetch('/deck/' + encodeURIComponent(_deckName) + '/card-data?name=' + encodeURIComponent(cardName))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) { setArtworkStatus('missing', 'Error: ' + data.error); return; }
                _serverData   = data;
                _originalJson = JSON.stringify(normaliseCard(data));
                populateForm(data);
                updateArtworkStatus(data._artwork_found, data._artwork_hint);
                updatePreview(data.image_base64);
                _currentTags = Array.isArray(data.tags) ? data.tags.slice() : [];
                _deckTags    = Array.isArray(data._deck_tags) ? data._deck_tags.slice() : [];
                renderTags();
                updateButtonStates();
                _updateCommanderBtn(_currentCardName);
            })
            .catch(function () { setArtworkStatus('missing', 'Failed to load card'); });
    }

    function openNewCardEditor() {
        _savedScrollY    = window.scrollY;
        _currentCardName = null;
        _isNewCard       = true;
        _editorIsDirty   = true;
        _originalJson    = '';
        _currentFace     = 'front';
        _faceCache       = { front: {}, back: {} };
        _serverData      = null;
        _setSubspellActive(false);

        $id('editor-card-title').textContent  = 'New Card';
        var scBtn = $id('set-commander-btn');
        if (scBtn) scBtn.style.display = 'none';
        var delBtn2 = $id('delete-card-btn');
        if (delBtn2) delBtn2.style.display = 'none';
        $id('cards-tab-main').style.display   = 'none';
        $id('card-editor-panel').style.display = '';

        switchEditorMode('form', true);
        history.replaceState(null, '', '#new-card');

        populateForm({ front: { name: '', mana: '', cardtype: 'Creature', subtype: '', rules: '', power: '', toughness: '' }, rarity: 'common', quantity: 1 });
        setArtworkStatus('', '');
        updatePreview(null);
        updateButtonStates();
    }

    function closeCardEditor(updateHash) {
        _currentCardName = null;
        _isNewCard       = false;
        _editorIsDirty   = false;
        _currentFace     = 'front';
        _faceCache       = { front: {}, back: {} };
        _serverData      = null;
        _setSubspellActive(false);
        _activateMultiSection(null, []);

        // Clear stale data so the next opened card doesn't briefly flash old content
        _currentTags = [];
        _deckTags    = [];
        renderTags();
        closeTagPicker();
        updatePreview(null);
        setArtworkStatus('', '');
        $id('editor-card-title').textContent = '';
        var scBtn = $id('set-commander-btn');
        if (scBtn) scBtn.style.display = 'none';
        var delBtnC = $id('delete-card-btn');
        if (delBtnC) delBtnC.style.display = 'none';

        $id('card-editor-panel').style.display = 'none';
        $id('cards-tab-main').style.display    = '';

        if (updateHash !== false) history.replaceState(null, '', '#cards');

        // Re-apply grouping/filtering so tag changes made in the editor take effect
        applyCardControls();

        // Restore scroll position from before the editor was opened
        window.scrollTo({ top: _savedScrollY, behavior: 'instant' });
    }

    // ── Real Card Dialog ──────────────────────────────────────────────────────

    function openRealCardDialogAdd() {
        _rcdMode            = 'add';
        _rcdSelectedCard    = null;
        _rcdSelectedPrinting = null;
        _rcdCardBeingEdited = null;

        var dialog = $id('real-card-dialog');
        if (!dialog) return;

        $id('rcd-title').textContent              = 'Add Real Card';
        $id('rcd-search-section').style.display   = '';
        $id('rcd-card-name-row').style.display    = 'none';
        $id('rcd-printing-section').style.display = 'none';
        var addBtn = $id('rcd-add-btn');
        if (addBtn) { addBtn.textContent = 'Add to Deck'; addBtn.disabled = true; }
        var delBtn = $id('rcd-delete-btn');
        if (delBtn) delBtn.style.display = 'none';
        $id('rcd-quantity').value = '1';
        $id('rcd-search-input').value = '';
        $id('rcd-search-results').innerHTML = '';
        $id('rcd-search-results').style.display = 'none';
        $id('rcd-search-status').style.display = 'none';
        _rcdClearStatus();

        dialog.showModal();
        setTimeout(function () { var inp = $id('rcd-search-input'); if (inp) inp.focus(); }, 50);
    }

    function openRealCardEditorForCard(cardName) {
        _rcdMode            = 'edit';
        _rcdSelectedCard    = null;
        _rcdSelectedPrinting = null;
        _rcdCardBeingEdited = cardName;

        var dialog = $id('real-card-dialog');
        if (!dialog) return;

        $id('rcd-title').textContent              = 'Edit Real Card';
        $id('rcd-search-section').style.display   = 'none';
        $id('rcd-card-name-row').style.display    = '';
        $id('rcd-card-name-display').textContent  = cardName;
        $id('rcd-printing-section').style.display = '';
        $id('rcd-printing-list').innerHTML        = '';
        $id('rcd-printings-loading').style.display = '';
        $id('rcd-preview-img').style.display       = 'none';
        $id('rcd-preview-placeholder').style.display = '';
        $id('rcd-preview-placeholder').textContent   = 'Select a printing';
        var addBtn = $id('rcd-add-btn');
        if (addBtn) { addBtn.textContent = 'Update Card'; addBtn.disabled = true; }
        var delBtn = $id('rcd-delete-btn');
        if (delBtn) delBtn.style.display = '';
        _rcdClearStatus();

        var galItem = document.querySelector('.card-gallery-item[data-card-name="' + cardName.replace(/"/g, '\\"') + '"]');
        var qtyEl = $id('rcd-quantity');
        if (qtyEl) qtyEl.value = galItem ? (parseInt(galItem.dataset.quantity, 10) || 1) : 1;

        dialog.showModal();

        fetch('/deck/' + encodeURIComponent(_deckName) + '/card-data?name=' + encodeURIComponent(cardName))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                _rcdSelectedCard = { name: cardName };
                _rcdLoadPrintings(cardName, data.scryfall_id || null);
            })
            .catch(function () { _rcdShowStatus('error', 'Failed to load card data.'); });
    }

    function _rcdClearStatus() {
        var el = $id('rcd-status');
        if (!el) return;
        el.style.display = 'none'; el.textContent = ''; el.className = 'rcd-status';
    }

    function _rcdShowStatus(type, msg) {
        var el = $id('rcd-status');
        if (!el) return;
        el.textContent = msg; el.className = 'rcd-status rcd-status--' + type; el.style.display = '';
    }

    function _rcdGetColors() {
        var colors = '';
        ['w', 'u', 'b', 'r', 'g'].forEach(function (c) {
            var cb = $id('rcd-color-' + c);
            if (cb && cb.checked) colors += c;
        });
        return colors || 'wubrg';
    }

    function _rcdDoSearch() {
        var q = ($id('rcd-search-input').value || '').trim();
        var statusEl  = $id('rcd-search-status');
        var resultsEl = $id('rcd-search-results');
        if (q.length < 2) { resultsEl.style.display = 'none'; statusEl.style.display = 'none'; return; }

        statusEl.textContent = 'Searching\u2026'; statusEl.style.display = '';
        resultsEl.style.display = 'none';

        fetch('/api/scryfall/search?q=' + encodeURIComponent(q) + '&colors=' + encodeURIComponent(_rcdGetColors()))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                statusEl.style.display = 'none';
                var cards = data.cards || [];
                resultsEl.innerHTML = '';
                if (cards.length === 0) {
                    resultsEl.innerHTML = '<div class="rcd-no-results">No cards found.</div>';
                    resultsEl.style.display = ''; return;
                }
                cards.forEach(function (card) {
                    var item = document.createElement('div');
                    item.className = 'rcd-result-item';
                    var nameEl = document.createElement('span');
                    nameEl.className = 'rcd-result-name'; nameEl.textContent = card.name;
                    var typeEl = document.createElement('span');
                    typeEl.className = 'rcd-result-type'; typeEl.textContent = card.type_line || '';
                    item.appendChild(nameEl); item.appendChild(typeEl);
                    item.addEventListener('click', function () { _rcdSelectCard(card); });
                    resultsEl.appendChild(item);
                });
                resultsEl.style.display = '';
            })
            .catch(function () { statusEl.textContent = 'Search failed. Check your connection.'; });
    }

    function _rcdSelectCard(card) {
        _rcdSelectedCard = card; _rcdSelectedPrinting = null;
        $id('rcd-search-results').style.display = 'none';
        $id('rcd-search-status').style.display  = 'none';
        $id('rcd-search-input').value = card.name;
        $id('rcd-printing-section').style.display    = '';
        $id('rcd-printing-list').innerHTML           = '';
        $id('rcd-printings-loading').style.display   = '';
        $id('rcd-preview-img').style.display         = 'none';
        $id('rcd-preview-placeholder').style.display = '';
        $id('rcd-preview-placeholder').textContent   = 'Select a printing';
        var addBtn = $id('rcd-add-btn'); if (addBtn) addBtn.disabled = true;
        _rcdLoadPrintings(card.name, null);
    }

    function _rcdLoadPrintings(cardName, currentScryfallId) {
        fetch('/api/scryfall/printings?name=' + encodeURIComponent(cardName))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var loadingEl = $id('rcd-printings-loading');
                if (loadingEl) loadingEl.style.display = 'none';
                var listEl = $id('rcd-printing-list');
                listEl.innerHTML = '';
                var printings = data.printings || [];
                if (printings.length === 0) {
                    listEl.innerHTML = '<div class="rcd-no-results">No printings found.</div>'; return;
                }
                var preSelected = null;
                printings.forEach(function (printing) {
                    var item = document.createElement('div');
                    item.className = 'rcd-printing-item';
                    if (currentScryfallId && printing.id === currentScryfallId) {
                        item.classList.add('rcd-printing-item--selected');
                        preSelected = printing;
                    }
                    var setCode = document.createElement('span');
                    setCode.className = 'rcd-printing-set'; setCode.textContent = printing.set;
                    var setName = document.createElement('span');
                    setName.className = 'rcd-printing-name'; setName.textContent = printing.set_name;
                    var year = document.createElement('span');
                    year.className = 'rcd-printing-year';
                    year.textContent = printing.released_at ? printing.released_at.slice(0, 4) : '';
                    var artist = document.createElement('span');
                    artist.className = 'rcd-printing-artist';
                    artist.textContent = printing.artist ? '\u2014 ' + printing.artist : '';
                    item.appendChild(setCode); item.appendChild(setName);
                    item.appendChild(year); item.appendChild(artist);
                    item.addEventListener('click', function () {
                        listEl.querySelectorAll('.rcd-printing-item').forEach(function (el) {
                            el.classList.remove('rcd-printing-item--selected');
                        });
                        item.classList.add('rcd-printing-item--selected');
                        _rcdSelectPrinting(printing);
                    });
                    listEl.appendChild(item);
                });
                if (preSelected) {
                    _rcdSelectedPrinting = preSelected;
                    _rcdUpdatePreview(preSelected.image_uri);
                    var addBtn = $id('rcd-add-btn'); if (addBtn) addBtn.disabled = false;
                }
            })
            .catch(function () {
                var loadingEl = $id('rcd-printings-loading');
                if (loadingEl) { loadingEl.textContent = 'Failed to load printings.'; }
            });
    }

    function _rcdSelectPrinting(printing) {
        _rcdSelectedPrinting = printing;
        _rcdUpdatePreview(printing.image_uri);
        var addBtn = $id('rcd-add-btn'); if (addBtn) addBtn.disabled = false;
    }

    function _rcdUpdatePreview(imageUri) {
        var img = $id('rcd-preview-img'), placeholder = $id('rcd-preview-placeholder');
        if (!imageUri) { if (img) img.style.display = 'none'; if (placeholder) placeholder.style.display = ''; return; }
        img.src = imageUri;
        img.onload  = function () { img.style.display = ''; if (placeholder) placeholder.style.display = 'none'; };
        img.onerror = function () {
            img.style.display = 'none';
            if (placeholder) { placeholder.style.display = ''; placeholder.textContent = 'Image unavailable'; }
        };
    }

    function _rcdSubmit() {
        if (!_rcdSelectedPrinting) return;
        var addBtn = $id('rcd-add-btn'); if (addBtn) addBtn.disabled = true;
        _rcdClearStatus();

        var cardName = _rcdMode === 'edit' ? _rcdCardBeingEdited : (_rcdSelectedCard ? _rcdSelectedCard.name : '');
        if (!cardName) { _rcdShowStatus('error', 'No card selected.'); if (addBtn) addBtn.disabled = false; return; }
        var qty = parseInt(($id('rcd-quantity') || {}).value, 10) || 1;
        var p   = _rcdSelectedPrinting;

        fetch('/deck/' + encodeURIComponent(_deckName) + '/add-real-card', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: cardName, image_uri: p.image_uri, quantity: qty,
                scryfall_id: p.id, oracle_id: p.oracle_id,
                mana_cost: p.mana_cost, type_line: p.type_line, oracle_text: p.oracle_text,
                power: p.power, toughness: p.toughness,
                colors: p.colors, color_identity: p.color_identity,
                rarity: p.rarity, set: p.set, set_name: p.set_name, artist: p.artist,
            }),
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (addBtn) addBtn.disabled = false;
            if (data.error) { _rcdShowStatus('error', 'Error: ' + data.error); return; }
            _updatePublishBar(data.staged_count || 0);
            if (_rcdMode === 'add') {
                _rcdAddGalleryItem(cardName, qty, p, data);
                _rcdShowStatus('ok', '\u2713 \u201c' + cardName + '\u201d added! Publish the Assembly Line to finalize.');
            } else {
                _rcdUpdateGalleryItem(cardName, qty, data);
                _rcdShowStatus('ok', '\u2713 \u201c' + cardName + '\u201d updated!');
            }
            setTimeout(function () {
                var dialog = $id('real-card-dialog');
                if (dialog && dialog.open) dialog.close();
            }, 1800);
        })
        .catch(function () {
            if (addBtn) addBtn.disabled = false;
            _rcdShowStatus('error', 'Request failed. Please try again.');
        });
    }

    function _rcdAddGalleryItem(cardName, qty, printing, serverData) {
        var typeLine = printing.type_line || '';
        var cardtype = typeLine.includes('\u2014') ? typeLine.split('\u2014')[0].trim() : typeLine;
        cardtype     = cardtype.replace(/\b(Legendary|Basic|Snow)\b/g, '').trim();
        var subtype  = typeLine.includes('\u2014') ? typeLine.split('\u2014')[1].trim() : '';

        var gallery = document.querySelector('#cards-tab-main .card-gallery');
        if (!gallery) return;

        var a = document.createElement('a');
        a.href = '#edit/' + encodeURIComponent(cardName);
        a.className = 'card-gallery-item';
        a.dataset.cardName = cardName; a.dataset.name = cardName;
        a.dataset.cost = printing.mana_cost || '';
        a.dataset.cardtype = cardtype; a.dataset.subtype = subtype;
        a.dataset.quantity = String(qty); a.dataset.real = '1'; a.dataset.staged = 'true';

        var container;
        if (serverData && serverData.image_base64) {
            container = document.createElement('div');
            container.className = 'card-image-container';
            var img = document.createElement('img');
            img.src = serverData.image_base64; img.dataset.frontSrc = serverData.image_base64;
            img.alt = cardName; img.className = 'card-image';
            container.appendChild(img);
        } else {
            container = document.createElement('div');
            container.className = 'card-image-placeholder';
            var pname = document.createElement('div');
            pname.className = 'placeholder-text'; pname.textContent = cardName;
            container.appendChild(pname);
        }
        var overlay = document.createElement('div');
        overlay.className = 'staged-overlay'; overlay.innerHTML = 'AWAITING<br>ASSEMBLY LINE';
        container.appendChild(overlay);
        if (qty > 1) {
            var qtyBadge = document.createElement('div');
            qtyBadge.className = 'quantity-badge'; qtyBadge.textContent = 'x' + qty;
            container.appendChild(qtyBadge);
        }
        a.appendChild(container);
        gallery.appendChild(a);
        if (_canonicalCardItems) _canonicalCardItems.push(a);
        applyCardControls();

        var countHdr = $id('cards-count-header');
        if (countHdr) {
            var m = countHdr.textContent.match(/\d+/);
            countHdr.textContent = 'Cards (' + (m ? parseInt(m[0], 10) + qty : qty) + ')';
        }
    }

    function _rcdUpdateGalleryItem(cardName, qty, data) {
        var galItem = document.querySelector('.card-gallery-item[data-card-name="' + cardName.replace(/"/g, '\\"') + '"]');
        if (!galItem) return;
        galItem.dataset.quantity = String(qty);
        _markCanonicalItemStaged(cardName);
        var container = galItem.querySelector('.card-image-container') || galItem.querySelector('.card-image-placeholder');
        if (container) {
            var qtyBadge = container.querySelector('.quantity-badge');
            if (qty > 1) {
                if (!qtyBadge) { qtyBadge = document.createElement('div'); qtyBadge.className = 'quantity-badge'; container.appendChild(qtyBadge); }
                qtyBadge.textContent = 'x' + qty;
            } else if (qtyBadge) { qtyBadge.remove(); }
            if (data.image_base64) {
                var imgEl = galItem.querySelector('.card-image');
                if (imgEl) { imgEl.src = data.image_base64; imgEl.dataset.frontSrc = data.image_base64; }
            }
        }
    }

    // ── Form Population ───────────────────────────────────────────────────────
    function populateForm(data) {
        var frontFace;
        if (data.front) {
            // Backward compat: old JSONs store frame at top-level; inject into front face if not already set
            var frontRaw = Object.assign({}, data.front);
            if (!frontRaw.frame && data.frame) frontRaw.frame = data.frame;
            frontFace = buildFaceDict(frontRaw);
        } else {
            frontFace = buildFaceDict({
                name: data.name, mana: data.cost, cardtype: data.cardtype,
                subtype: data.subtype, rules: data.rules, power: data.power,
                toughness: data.toughness, flavor: data.flavor,
                legendary: data.legendary, basic: data.basic, snow: data.snow,
                frame: data.frame
            });
        }
        _faceCache   = { front: frontFace, back: buildFaceDict(data.back || {}) };
        _currentFace = 'front';
        var rarEl = $id('ef-rarity');
        if (rarEl) rarEl.value = (data.rarity || 'common').toLowerCase();
        var dfcEl = $id('ef-dfc-type');
        if (dfcEl) dfcEl.value = data.double_faced_type || '';
        var artistEl = $id('ef-artist');
        if (artistEl) artistEl.value = data.artist || '';
        var qtyEl = $id('ef-quantity');
        if (qtyEl) qtyEl.value = parseInt(data.quantity, 10) || 1;
        populateFaceForm(frontFace);
        _populateSubspell(data.subspell || null);
        updateFaceTabs();
    }

    // ── Serialise form → card JSON ────────────────────────────────────────────
    function serializeForm() {
        _faceCache[_currentFace] = captureCurrentFace();
        var rarEl   = $id('ef-rarity');
        var dfcEl   = $id('ef-dfc-type');
        var qtyEl   = $id('ef-quantity');
        var result = {
            front:    _faceCache.front,
            rarity:   rarEl ? rarEl.value : 'common',
            quantity: qtyEl ? (parseInt(qtyEl.value, 10) || 1) : 1
        };
        if (_faceCache.back && Object.keys(_faceCache.back).length > 0) {
            result.back = _faceCache.back;
        }
        var dfcVal = dfcEl ? dfcEl.value : '';
        if (dfcVal) result.double_faced_type = dfcVal;
        var artistEl = $id('ef-artist');
        var artistVal = artistEl ? artistEl.value.trim() : '';
        if (artistVal) result.artist = artistVal;
        var ss = _captureSubspell();
        if (ss) result.subspell = ss;
        return result;
    }

    // Normalise server card dict into canonical shape for dirty comparison
    function normaliseCard(data) {
        var frontFace;
        if (data.front) {
            // Backward compat: old JSONs store frame at top-level; inject into front face if not already set
            var frontRaw = Object.assign({}, data.front);
            if (!frontRaw.frame && data.frame) frontRaw.frame = data.frame;
            frontFace = buildFaceDict(frontRaw);
        } else {
            frontFace = buildFaceDict({
                name: data.name, mana: data.cost, cardtype: data.cardtype,
                subtype: data.subtype, rules: data.rules, power: data.power,
                toughness: data.toughness, flavor: data.flavor,
                legendary: data.legendary, basic: data.basic, snow: data.snow,
                frame: data.frame
            });
        }
        var result = { front: frontFace, rarity: (data.rarity || 'common').toLowerCase(), quantity: parseInt(data.quantity, 10) || 1 };
        if (data.back) {
            var backFace = buildFaceDict(data.back);
            if (Object.keys(backFace).length > 0) result.back = backFace;
        }
        if (data.double_faced_type) result.double_faced_type = data.double_faced_type;
        if (data.artist) result.artist = data.artist;
        if (data.subspell) {
            var normSs = {};
            _SS_FIELDS.forEach(function (k) { if (data.subspell[k]) normSs[k] = data.subspell[k]; });
            if (Object.keys(normSs).length > 0) result.subspell = normSs;
        }
        return result;
    }

    // ── Change Detection ──────────────────────────────────────────────────────
    function onFormChange() {
        if (!_currentCardName && !_isNewCard) return;
        _editorIsDirty = _isNewCard || (JSON.stringify(serializeForm()) !== _originalJson);
        updateButtonStates();
    }

    function onJsonChange() {
        if (!_currentCardName && !_isNewCard) return;
        var raw = _cmEditor ? _cmEditor.getValue() : (($id('editor-json-textarea') || {}).value || '{}');
        try {
            _editorIsDirty = _isNewCard || (JSON.stringify(normaliseCard(JSON.parse(raw))) !== _originalJson);
        } catch (e) { /* invalid JSON — preserve state */ }
        updateButtonStates();
    }

    function updateButtonStates() {
        var active = _editorIsDirty || _isNewCard;
        var forgeBtn = $id('forge-btn');
        if (forgeBtn) {
            forgeBtn.classList.toggle('btn-forge--active', active);
        }
    }

    // ── Editor Mode Toggle ────────────────────────────────────────────────────
    function switchEditorMode(mode, silent) {
        var jsonErr = $id('editor-json-error');
        if (jsonErr) { jsonErr.style.display = 'none'; jsonErr.textContent = ''; }

        if (mode === 'json') {
            // Sync form → JSON text
            if (!silent || _editorMode !== 'json') {
                var jsonStr = JSON.stringify(serializeForm(), null, 2);
                if (_cmEditor) {
                    _cmEditor.setValue(jsonStr);
                } else {
                    var ta = $id('editor-json-textarea');
                    if (ta) ta.value = jsonStr;
                }
            }
            // Lazy-init CodeMirror on first switch
            if (!_cmEditor && window.CodeMirror) {
                var ta2 = $id('editor-json-textarea');
                if (ta2) {
                    var existing = ta2.value;
                    _cmEditor = window.CodeMirror.fromTextArea(ta2, {
                        mode: 'application/json',
                        lineNumbers: true,
                        matchBrackets: true,
                        theme: 'default',
                        lineWrapping: true
                    });
                    _cmEditor.setValue(existing);
                    _cmEditor.on('change', onJsonChange);
                }
            }
            $id('editor-form-mode').style.display = 'none';
            $id('editor-json-mode').style.display = '';
            if (_cmEditor) setTimeout(function () { _cmEditor.refresh(); }, 10);

        } else {
            // Sync JSON → form (unless silent)
            if (!silent && _editorMode === 'json') {
                var raw = _cmEditor ? _cmEditor.getValue() : (($id('editor-json-textarea') || {}).value || '{}');
                try {
                    populateForm(JSON.parse(raw));
                } catch (e) {
                    if (jsonErr) { jsonErr.textContent = 'Invalid JSON — fix before switching: ' + e.message; jsonErr.style.display = ''; }
                    return;
                }
            }
            $id('editor-form-mode').style.display = '';
            $id('editor-json-mode').style.display = 'none';
        }

        _editorMode = mode;
        document.querySelectorAll('.editor-mode-btn').forEach(function (btn) {
            btn.classList.toggle('editor-mode-btn--active', btn.dataset.mode === mode);
        });
    }

    // ── Artwork & Preview ─────────────────────────────────────────────────────
    function updateArtworkStatus(found, hint) {
        var el = $id('artwork-status');
        if (!el) return;
        if (found) {
            el.textContent = '\u2713 Artwork: ' + hint;
            el.className   = 'artwork-status artwork-status--found';
        } else {
            el.textContent = '\u26a0 No artwork';
            el.className   = 'artwork-status artwork-status--missing';
        }
    }

    function setArtworkStatus(type, msg) {
        var el = $id('artwork-status');
        if (!el) return;
        el.textContent = msg;
        el.className   = 'artwork-status' + (type ? ' artwork-status--' + type : '');
    }

    function updatePreview(base64) {
        var img = $id('editor-card-preview');
        var ph  = $id('editor-card-placeholder');
        if (base64) {
            if (img) {
                // Clear src first so the browser always treats the new data as a
                // fresh load, even if the base64 content happens to be identical
                // to the previously displayed image (e.g. consecutive forges).
                img.src = '';
                img.src = base64;
                img.style.display = '';
            }
            if (ph)  ph.style.display = 'none';
        } else {
            if (img) img.style.display = 'none';
            if (ph)  ph.style.display = '';
        }
    }

    // ── Tags ──────────────────────────────────────────────────────────────────

    function renderTags() {
        var list = $id('editor-tag-list');
        if (!list) return;
        list.innerHTML = '';
        _currentTags.forEach(function (tag) {
            var chip = document.createElement('span');
            chip.className = 'editor-tag-chip';
            chip.textContent = tag;
            var x = document.createElement('button');
            x.className = 'editor-tag-remove';
            x.type = 'button';
            x.textContent = '×';
            x.title = 'Remove tag';
            x.addEventListener('click', function () { doRemoveTag(tag); });
            chip.appendChild(x);
            list.appendChild(chip);
        });
    }

    function openTagPicker() {
        var picker = $id('tag-picker');
        var input  = $id('tag-picker-input');
        if (!picker || !input) return;
        picker.style.display = '';
        input.value = '';
        renderTagOptions('');
        input.focus();
    }

    function closeTagPicker() {
        var picker = $id('tag-picker');
        if (picker) picker.style.display = 'none';
    }

    function renderTagOptions(filter) {
        var opts = $id('tag-picker-options');
        if (!opts) return;
        opts.innerHTML = '';
        var q = filter.trim().toLowerCase();
        var candidates = _deckTags.filter(function (t) {
            return !_currentTags.includes(t) && (!q || t.toLowerCase().includes(q));
        });
        candidates.forEach(function (tag) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'tag-picker-option';
            btn.textContent = tag;
            btn.addEventListener('mousedown', function (e) {
                e.preventDefault();
                doAddTag(tag);
            });
            opts.appendChild(btn);
        });
        // "Create new" option when typed text is non-empty and not an exact existing match
        if (filter.trim() && !_deckTags.map(function (t) { return t.toLowerCase(); }).includes(filter.trim().toLowerCase())) {
            var newBtn = document.createElement('button');
            newBtn.type = 'button';
            newBtn.className = 'tag-picker-option tag-picker-option--new';
            newBtn.textContent = 'Create new tag: "' + filter.trim() + '"';
            newBtn.addEventListener('mousedown', function (e) {
                e.preventDefault();
                doAddTag(filter.trim());
            });
            opts.appendChild(newBtn);
        }
    }

    // Always marks the CANONICAL gallery item as staged (not a clone).
    // querySelector may find a clone first (e.g. "Artifact Creature" appears in
    // both Creature and Artifact groups). applyCardControls rebuilds from canonical
    // items, so the canonical item must carry the staged state.
    function _markCanonicalItemStaged(cardName) {
        var canonical = getCanonicalItems().find(function (ci) {
            return ci.dataset.cardName === cardName;
        });
        if (!canonical) return;
        canonical.dataset.staged = 'true';
        var con = canonical.querySelector('.card-image-container, .card-image-placeholder');
        if (con && !con.querySelector('.staged-overlay')) {
            var ov = document.createElement('div');
            ov.className = 'staged-overlay';
            ov.innerHTML = 'AWAITING<br>ASSEMBLY LINE';
            con.appendChild(ov);
        }
    }

    function _updateGalleryItemTags(cardName, tags) {
        var item = document.querySelector('.card-gallery-item[data-card-name="' + CSS.escape(cardName) + '"]');
        if (item) item.dataset.tags = tags.join(',');
    }

    function doAddTag(tag) {
        if (!tag || !_currentCardName) return;
        closeTagPicker();
        fetch('/deck/' + encodeURIComponent(_deckName) + '/add-card-tag?name=' + encodeURIComponent(_currentCardName), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag: tag })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.error) return;
            _currentTags = data.card_tags;
            _deckTags    = data.deck_tags;
            renderTags();
            _updateGalleryItemTags(_currentCardName, _currentTags);
        })
        .catch(function () {});
    }

    function doRemoveTag(tag) {
        if (!tag || !_currentCardName) return;
        fetch('/deck/' + encodeURIComponent(_deckName) + '/remove-card-tag?name=' + encodeURIComponent(_currentCardName), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag: tag })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.error) return;
            _currentTags = data.card_tags;
            _deckTags    = data.deck_tags;
            renderTags();
            _updateGalleryItemTags(_currentCardName, _currentTags);
        })
        .catch(function () {});
    }

    // ── Edit Tags Dialog ──────────────────────────────────────────────────────

    function openEditTagsDialog() {
        var dialog = $id('edit-tags-dialog');
        if (!dialog) return;
        var list = $id('edit-tags-list');
        if (list) list.innerHTML = '<p class="edit-tags-empty">Loading\u2026</p>';
        dialog.showModal();
        fetch('/deck/' + encodeURIComponent(_deckName) + '/tags-data')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) {
                    if (list) list.innerHTML = '<p class="edit-tags-empty">' + data.error + '</p>';
                    return;
                }
                _renderEditTagsList(data.tags);
            })
            .catch(function () {
                if (list) list.innerHTML = '<p class="edit-tags-empty">Failed to load tags.</p>';
            });
    }

    function _renderEditTagsList(tags) {
        var list = $id('edit-tags-list');
        if (!list) return;
        if (!tags || tags.length === 0) {
            list.innerHTML = '<p class="edit-tags-empty">No tags in this deck yet.</p>';
            return;
        }
        list.innerHTML = '';
        tags.forEach(function (tagObj) {
            list.appendChild(_buildEditTagRow(tagObj));
        });
    }

    function _buildEditTagRow(tagObj) {
        var originalName = tagObj.name;
        var cardCount    = tagObj.card_count || 0;

        var row = document.createElement('div');
        row.className = 'edit-tag-row';

        // ── Main row: input + count + Rename + Remove ──
        var mainRow = document.createElement('div');
        mainRow.className = 'edit-tag-main';

        var input = document.createElement('input');
        input.type = 'text';
        input.className = 'edit-tag-input';
        input.value = originalName;

        var countEl = document.createElement('span');
        countEl.className = 'edit-tag-count';
        countEl.textContent = cardCount + (cardCount === 1 ? ' card' : ' cards');

        var renameBtn = document.createElement('button');
        renameBtn.className = 'btn-tag-rename';
        renameBtn.textContent = 'Rename';
        renameBtn.disabled = true;

        var deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn-tag-delete';
        deleteBtn.textContent = 'Remove';

        mainRow.appendChild(input);
        mainRow.appendChild(countEl);
        mainRow.appendChild(renameBtn);
        mainRow.appendChild(deleteBtn);

        // ── Add by card text row ──
        var byTextRow = document.createElement('div');
        byTextRow.className = 'edit-tag-by-text';

        var label = document.createElement('span');
        label.className = 'edit-tag-by-text-label';
        label.textContent = 'Add cards containing:';

        var textInput = document.createElement('input');
        textInput.type = 'text';
        textInput.className = 'edit-tag-text-input';
        textInput.placeholder = 'e.g. replicate';

        var addBtn = document.createElement('button');
        addBtn.className = 'btn-tag-add-by-text';
        addBtn.textContent = 'Find & Add';
        addBtn.disabled = true;

        byTextRow.appendChild(label);
        byTextRow.appendChild(textInput);
        byTextRow.appendChild(addBtn);

        // ── Feedback line ──
        var feedback = document.createElement('div');
        feedback.className = 'edit-tag-feedback';

        row.appendChild(mainRow);
        row.appendChild(byTextRow);
        row.appendChild(feedback);

        // ── Behaviour: rename button enables when input changes ──
        input.addEventListener('input', function () {
            renameBtn.disabled = (input.value.trim() === originalName || input.value.trim() === '');
        });

        renameBtn.addEventListener('click', function () {
            var newName = input.value.trim();
            if (!newName || newName === originalName) return;
            renameBtn.disabled = true;
            renameBtn.textContent = '\u2026';
            fetch('/deck/' + encodeURIComponent(_deckName) + '/rename-tag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_tag: originalName, new_tag: newName })
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                renameBtn.textContent = 'Rename';
                if (data.error) {
                    feedback.textContent = 'Error: ' + data.error;
                    feedback.style.color = '#e53935';
                    renameBtn.disabled = false;
                    return;
                }
                feedback.textContent = 'Renamed \u2014 ' + data.affected_cards + ' card' + (data.affected_cards !== 1 ? 's' : '') + ' updated.';
                feedback.style.color = '#43a047';
                // Patch data-tags on every gallery item that carried the old tag
                var oldName = originalName;
                document.querySelectorAll('.card-item[data-tags]').forEach(function (item) {
                    var tags = (item.dataset.tags || '').split(',').filter(Boolean);
                    var idx = tags.indexOf(oldName);
                    if (idx !== -1) { tags[idx] = newName; item.dataset.tags = tags.join(','); }
                });
                _deckTags = data.deck_tags;
                originalName = newName;
                renameBtn.disabled = true;
                countEl.textContent = data.affected_cards + (data.affected_cards === 1 ? ' card' : ' cards');
                applyCardControls();
            })
            .catch(function () {
                renameBtn.textContent = 'Rename';
                renameBtn.disabled = false;
                feedback.textContent = 'Request failed.';
                feedback.style.color = '#e53935';
            });
        });

        deleteBtn.addEventListener('click', function () {
            if (!confirm('Remove tag \u201c' + originalName + '\u201d from all ' + cardCount + ' card(s)?')) return;
            deleteBtn.disabled = true;
            fetch('/deck/' + encodeURIComponent(_deckName) + '/delete-tag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag: originalName })
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) {
                    deleteBtn.disabled = false;
                    feedback.textContent = 'Error: ' + data.error;
                    feedback.style.color = '#e53935';
                    return;
                }
                // Strip deleted tag from every gallery item
                var removedTag = originalName;
                document.querySelectorAll('.card-item[data-tags]').forEach(function (item) {
                    var tags = (item.dataset.tags || '').split(',').filter(function (t) { return t !== removedTag; });
                    item.dataset.tags = tags.join(',');
                });
                _deckTags = data.deck_tags;
                applyCardControls();
                // Animate row out
                row.style.transition = 'opacity 0.2s';
                row.style.opacity = '0';
                setTimeout(function () {
                    if (row.parentNode) row.parentNode.removeChild(row);
                    var list = $id('edit-tags-list');
                    if (list && list.children.length === 0) {
                        list.innerHTML = '<p class="edit-tags-empty">No tags in this deck yet.</p>';
                    }
                }, 220);
            })
            .catch(function () {
                deleteBtn.disabled = false;
                feedback.textContent = 'Request failed.';
                feedback.style.color = '#e53935';
            });
        });

        // ── Behaviour: Find & Add button enables when text input has content ──
        textInput.addEventListener('input', function () {
            addBtn.disabled = (textInput.value.trim() === '');
        });

        addBtn.addEventListener('click', function () {
            var text = textInput.value.trim();
            if (!text) return;
            addBtn.disabled = true;
            addBtn.textContent = '\u2026';
            fetch('/deck/' + encodeURIComponent(_deckName) + '/add-cards-by-text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag: originalName, text: text })
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                addBtn.textContent = 'Find & Add';
                addBtn.disabled = (textInput.value.trim() === '');
                if (data.error) {
                    feedback.textContent = 'Error: ' + data.error;
                    feedback.style.color = '#e53935';
                    return;
                }
                var added = data.added_cards.length;
                var skipped = data.already_had_tag.length;
                if (added === 0 && skipped === 0) {
                    feedback.textContent = 'No cards matched \u201c' + text + '\u201d.';
                    feedback.style.color = '#888';
                } else if (added === 0) {
                    feedback.textContent = 'All matching cards already have this tag.';
                    feedback.style.color = '#888';
                } else {
                    feedback.textContent = 'Added to ' + added + ' card' + (added !== 1 ? 's' : '') +
                        (skipped ? ' (' + skipped + ' already tagged)' : '') + '.';
                    feedback.style.color = '#43a047';
                    // Update card count display
                    cardCount += added;
                    countEl.textContent = cardCount + (cardCount === 1 ? ' card' : ' cards');
                    _deckTags = data.deck_tags;
                    // Update gallery data-tags for affected cards
                    data.added_cards.forEach(function (cardName) {
                        var item = document.querySelector('.card-item[data-name="' + CSS.escape(cardName) + '"]');
                        if (item) {
                            var existing = (item.dataset.tags || '').split(',').filter(Boolean);
                            if (!existing.includes(originalName)) {
                                existing.push(originalName);
                                item.dataset.tags = existing.join(',');
                            }
                        }
                    });
                    applyCardControls();
                }
            })
            .catch(function () {
                addBtn.textContent = 'Find & Add';
                addBtn.disabled = (textInput.value.trim() === '');
                feedback.textContent = 'Request failed.';
                feedback.style.color = '#e53935';
            });
        });

        return row;
    }

    // ── Forge ─────────────────────────────────────────────────────────────────
    function getEditorJson() {
        // Return current card dict regardless of editor mode (form or JSON).
        if (_editorMode === 'json') {
            var raw = _cmEditor ? _cmEditor.getValue()
                                : (($id('editor-json-textarea') || {}).value || '{}');
            try { return JSON.parse(raw); }
            catch (e) {
                setArtworkStatus('missing', 'Invalid JSON: ' + e.message);
                return null;
            }
        }
        return serializeForm();
    }

    function onForgeClick() {
        var cardData = getEditorJson();
        if (!cardData) return;

        var url = '/deck/' + encodeURIComponent(_deckName) + '/forge-card?name='
            + encodeURIComponent(_currentCardName || '_new');

        // Disable forge button while request is in flight
        var forgeBtn = $id('forge-btn');
        if (forgeBtn) forgeBtn.disabled = true;
        setArtworkStatus('found', 'Forging\u2026');

        fetch(url, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(cardData)
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.error) {
                setArtworkStatus('missing', 'Forge failed: ' + data.error);
                if (forgeBtn) forgeBtn.disabled = false;
                updateButtonStates();
                return;
            }

            // Update assembly badge + publish bar count/button
            _updatePublishBar(data.staged_count || 0);

            // Helper: update the gallery quantity badge for the current card
            function _updateGalleryQtyBadge(cardName, qty) {
                if (!cardName) return;
                var galItem = document.querySelector('.card-gallery-item[data-card-name="' + cardName.replace(/"/g, '\\"') + '"]');
                if (!galItem) return;
                galItem.dataset.quantity = qty;
                var container = galItem.querySelector('.card-image-container') ||
                                galItem.querySelector('.card-image-placeholder');
                if (container) {
                    var badge = container.querySelector('.quantity-badge');
                    if (qty > 1) {
                        if (badge) { badge.textContent = 'x' + qty; }
                        else {
                            var nb = document.createElement('div');
                            nb.className = 'quantity-badge';
                            nb.textContent = 'x' + qty;
                            container.appendChild(nb);
                        }
                    } else {
                        if (badge) badge.remove();
                    }
                }
                applyCardControls();
            }

            // Quantity-only change: quantity saved directly to deck JSON, no staging needed
            if (data.quantity_only_change) {
                _updateGalleryQtyBadge(_currentCardName, data.quantity || 1);
                _editorIsDirty = false;
                _originalJson  = JSON.stringify(serializeForm());
                setArtworkStatus('found', 'Quantity saved \u2713');
                if (forgeBtn) forgeBtn.disabled = false;
                updateButtonStates();
                return;
            }

            // Update card preview (respect current face tab)
            var previewB64 = (_currentFace === 'back' && data.back_image_base64)
                ? data.back_image_base64
                : data.image_base64;
            if (previewB64) updatePreview(previewB64);

            // Update _serverData so face switching shows the freshly forged images
            if (_serverData) {
                if (data.image_base64) _serverData.image_base64 = data.image_base64;
                if (data.back_image_base64) _serverData.back_image_base64 = data.back_image_base64;
            }

            // New card now exists in the deck — track its name
            if (_isNewCard && cardData.front && cardData.front.name) {
                _currentCardName = cardData.front.name;
                _isNewCard       = false;
            }
            // Card may have been renamed (e.g. subspell added/changed)
            if (data.new_card_name) {
                var prevCardName = _currentCardName;
                _currentCardName = data.new_card_name;
                $id('editor-card-title').textContent = data.new_card_name;
                history.replaceState(null, '', '#edit/' + encodeURIComponent(data.new_card_name));
                // Update the gallery item so it can be re-opened correctly after rename
                if (prevCardName) {
                    var renamedGalItem = document.querySelector('.card-gallery-item[data-card-name="' + prevCardName.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"]');
                    if (renamedGalItem) {
                        renamedGalItem.dataset.cardName = data.new_card_name;
                        renamedGalItem.dataset.name     = data.new_card_name;
                        renamedGalItem.setAttribute('href', '#edit/' + encodeURIComponent(data.new_card_name));
                        var phEl = renamedGalItem.querySelector('.placeholder-text');
                        if (phEl) phEl.textContent = data.new_card_name;
                    }
                }
            }

            _editorIsDirty = false;
            _originalJson  = JSON.stringify(serializeForm());
            setArtworkStatus('found', 'Forged \u2713');
            if (forgeBtn) forgeBtn.disabled = false;
            updateButtonStates();

            // Update gallery quantity badge
            _updateGalleryQtyBadge(_currentCardName, cardData.quantity || 1);

            // Mark the canonical gallery item as staged
            if (_currentCardName) {
                _markCanonicalItemStaged(_currentCardName);
            }

        })
        .catch(function (err) {
            console.error('Forge error:', err);
            setArtworkStatus('missing', 'Forge error \u2014 check server log');
            if (forgeBtn) forgeBtn.disabled = false;
            updateButtonStates();
        });
    }

    // ── Assembly Line ─────────────────────────────────────────────────────────
    function _updatePublishBar(count) {
        _stagedCount = count;
        var badge = $id('assembly-badge');
        if (badge) {
            badge.textContent = count;
            badge.classList.toggle('assembly-badge--active', count > 0);
        }
        var publishBtn    = $id('publish-assembly-btn');
        var publishEdBtn  = $id('publish-btn');
        var countSpan     = $id('publish-count');
        if (countSpan)   countSpan.textContent = count;
        if (publishBtn)  publishBtn.disabled   = (count === 0);
        if (publishEdBtn) publishEdBtn.disabled = (count === 0);
    }

    function loadAssemblyLineData() {
        var list    = $id('assembly-line-list');
        var loading = $id('assembly-loading');
        if (!list) return;
        if (loading) { loading.style.display = ''; }
        // Clear old rows (keep loading element)
        Array.from(list.children).forEach(function (child) {
            if (child.id !== 'assembly-loading') child.remove();
        });

        fetch('/deck/' + encodeURIComponent(_deckName) + '/assembly-line-data')
            .then(function (r) { return r.json(); })
            .then(function (items) {
                if (loading) loading.style.display = 'none';
                if (!items.length) {
                    var empty = document.createElement('div');
                    empty.className = 'tab-empty-state';
                    empty.innerHTML = '<p>No staged changes. Forge a card in the Cards tab to add it to the Assembly Line.</p>';
                    list.appendChild(empty);
                    return;
                }
                items.forEach(function (item) { list.appendChild(_buildAssemblyRow(item)); });
            })
            .catch(function () {
                if (loading) loading.style.display = 'none';
            });
    }

    // ── Flip button helpers ───────────────────────────────────────────────
    function _flipImgInner(innerEl) {
        // innerEl is an .assembly-img-inner; the img inside has data-front-src / data-back-src
        var img = innerEl.querySelector('img');
        if (!img) return;
        var isBack = innerEl.dataset.face === 'back';
        if (!isBack) {
            var backSrc = img.dataset.backSrc || '';
            if (backSrc) { img.src = backSrc; }
            innerEl.dataset.face = 'back';
        } else {
            var frontSrc = img.dataset.frontSrc || '';
            if (frontSrc) { img.src = frontSrc; }
            innerEl.dataset.face = 'front';
        }
    }

    function _handleAssemblyFlip(clickedInner, pairedInner) {
        // Flip the clicked inner; if both should stay in sync, flip paired too
        var clickedIsBack = clickedInner.dataset.face === 'back';
        var pairedIsBack = pairedInner ? pairedInner.dataset.face === 'back' : null;
        // If paired exists and both are on same face, flip together
        if (pairedInner) {
            if (clickedIsBack === pairedIsBack) {
                _flipImgInner(clickedInner);
                _flipImgInner(pairedInner);
            } else {
                // Out of sync — just sync them both to clicked's new state
                _flipImgInner(clickedInner);
                // Force paired to match new state of clicked
                var newFace = clickedInner.dataset.face;
                var pairedImg = pairedInner.querySelector('img');
                if (pairedImg) {
                    pairedImg.src = newFace === 'back'
                        ? (pairedImg.dataset.backSrc || pairedImg.dataset.frontSrc || '')
                        : (pairedImg.dataset.frontSrc || '');
                    pairedInner.dataset.face = newFace;
                }
            }
        } else {
            _flipImgInner(clickedInner);
        }
    }

    function _handleGalleryFlip(flipBtn) {
        var container = flipBtn.closest('.card-image-container');
        if (!container) return;
        var img = container.querySelector('.card-image');
        if (!img) return;

        var isBack = container.dataset.face === 'back';
        if (!isBack) {
            var backSrc = img.dataset.backSrc || '';
            if (backSrc) {
                img.src = backSrc;
            } else {
                // No back image rendered yet — show a placeholder overlay
                var overlay = container.querySelector('.card-flip-no-image');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.className = 'card-flip-no-image';
                    overlay.textContent = 'No Image';
                    container.appendChild(overlay);
                }
                overlay.style.display = 'flex';
                img.style.visibility = 'hidden';
            }
            container.dataset.face = 'back';
        } else {
            var frontSrc = img.dataset.frontSrc || '';
            if (frontSrc) {
                img.src = frontSrc;
                img.style.visibility = '';
            }
            var overlay2 = container.querySelector('.card-flip-no-image');
            if (overlay2) overlay2.style.display = 'none';
            container.dataset.face = 'front';
        }
    }

    function _buildAssemblyRow(item) {
        var row = document.createElement('div');
        row.className = 'assembly-card-row';
        row.dataset.cardName = item.card_name;

        // Header: card name (left) + discard button (right)
        var header = document.createElement('div');
        header.className = 'assembly-card-header';

        var label = document.createElement('div');
        label.className = 'assembly-card-label' + (item.pending_delete ? ' assembly-card-label--delete' : '');
        label.textContent = item.card_name + (item.is_new ? ' (new)' : '') + (item.pending_delete ? ' — pending delete' : '');
        label.title = item.card_name;

        var discardBtn = document.createElement('button');
        discardBtn.className = 'btn assembly-discard-btn';
        discardBtn.textContent = 'Discard';
        discardBtn.addEventListener('click', function () { onDiscardCard(item.card_name, row); });

        header.appendChild(label);
        header.appendChild(discardBtn);

        // Images: original → staged
        var images = document.createElement('div');
        images.className = 'assembly-card-images';

        var origHasBack = !!(item.original_back_image_base64);
        var stgHasBack = !!(item.staged_back_image_base64);
        var bothHaveBack = origHasBack && stgHasBack;

        // Original image
        var origWrap = document.createElement('div');
        origWrap.className = 'assembly-img-wrap';
        var origCaption = document.createElement('div');
        origCaption.className = 'assembly-img-caption';
        origCaption.textContent = item.is_new ? 'New' : 'Original';
        if (item.original_image_base64 && !item.is_new) {
            var origImgEl = document.createElement('div');
            origImgEl.className = 'assembly-img-inner';
            var origImg = document.createElement('img');
            origImg.src = item.original_image_base64;
            origImg.dataset.frontSrc = item.original_image_base64;
            origImg.dataset.backSrc = item.original_back_image_base64 || '';
            origImg.className = 'assembly-card-img';
            origImg.alt = 'Original';
            origImgEl.appendChild(origImg);
            if (origHasBack) {
                var origFlipBtn = document.createElement('button');
                origFlipBtn.className = 'card-flip-btn assembly-flip-btn';
                origFlipBtn.title = 'Flip card';
                origFlipBtn.type = 'button';
                origFlipBtn.textContent = '↻';
                origFlipBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    _handleAssemblyFlip(origImgEl, stgHasBack && bothHaveBack ? stgImgEl : null);
                });
                origImgEl.appendChild(origFlipBtn);
            }
            origWrap.appendChild(origImgEl);
        } else {
            var origPlaceholder = document.createElement('div');
            origPlaceholder.className = 'assembly-card-placeholder';
            origPlaceholder.textContent = item.is_new ? (item.is_real ? 'New Real Card' : 'New Card') : 'No Image';
            origWrap.appendChild(origPlaceholder);
        }
        origWrap.appendChild(origCaption);

        var arrow = document.createElement('div');
        arrow.className = 'assembly-arrow';
        arrow.textContent = '→';

        // Staged image — declare stgImgEl in scope so origFlipBtn closure can reference it
        var stgImgEl;
        var stgWrap = document.createElement('div');
        stgWrap.className = 'assembly-img-wrap';
        var stgCaption = document.createElement('div');
        stgCaption.className = 'assembly-img-caption';
        stgCaption.textContent = item.pending_delete ? 'Result' : 'Staged';
        if (item.pending_delete) {
            var deleteBanner = document.createElement('div');
            deleteBanner.className = 'assembly-delete-banner';
            deleteBanner.textContent = '✕ DELETED';
            stgWrap.appendChild(deleteBanner);
        } else if (item.staged_image_base64) {
            stgImgEl = document.createElement('div');
            stgImgEl.className = 'assembly-img-inner';
            var stgImg = document.createElement('img');
            stgImg.src = item.staged_image_base64;
            stgImg.dataset.frontSrc = item.staged_image_base64;
            stgImg.dataset.backSrc = item.staged_back_image_base64 || '';
            stgImg.className = 'assembly-card-img';
            stgImg.alt = 'Staged';
            stgImgEl.appendChild(stgImg);
            if (stgHasBack) {
                var stgFlipBtn = document.createElement('button');
                stgFlipBtn.className = 'card-flip-btn assembly-flip-btn';
                stgFlipBtn.title = 'Flip card';
                stgFlipBtn.type = 'button';
                stgFlipBtn.textContent = '↻';
                stgFlipBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    _handleAssemblyFlip(stgImgEl, origHasBack && bothHaveBack ? origImgEl : null);
                });
                stgImgEl.appendChild(stgFlipBtn);
            }
            stgWrap.appendChild(stgImgEl);
        } else {
            var stgPlaceholder = document.createElement('div');
            stgPlaceholder.className = 'assembly-card-placeholder';
            stgPlaceholder.textContent = 'No Image';
            stgWrap.appendChild(stgPlaceholder);
        }
        stgWrap.appendChild(stgCaption);

        images.appendChild(origWrap);
        images.appendChild(arrow);
        images.appendChild(stgWrap);

        row.appendChild(header);
        row.appendChild(images);

        // Change summary message
        if (!item.is_new && !item.pending_delete) {
            var changeMsg = document.createElement('div');
            changeMsg.className = 'assembly-change-message';
            changeMsg.textContent = item.change_type === 'text_changed'
                ? 'Card text changed'
                : 'Possible artwork change';
            row.appendChild(changeMsg);
        }

        return row;
    }

    function onDiscardCard(cardName, rowEl) {
        fetch('/deck/' + encodeURIComponent(_deckName) + '/discard-card?name=' + encodeURIComponent(cardName), {
            method: 'POST',
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.error) return;
            if (rowEl) rowEl.remove();
            _updatePublishBar(data.staged_count || 0);
            // Update gallery item staged state (remove entirely for new cards since they no longer exist)
            var galItem = document.querySelector('.card-gallery-item[data-card-name="' + cardName.replace(/"/g, '\\"') + '"]');
            if (galItem) {
                if (data.is_new) {
                    galItem.remove();
                } else {
                    galItem.dataset.staged = 'false';
                    var ov = galItem.querySelector('.staged-overlay');
                    if (ov) ov.remove();
                }
            }
            // If list is now empty, show empty state
            var list = $id('assembly-line-list');
            if (list && !list.querySelector('.assembly-card-row')) {
                var empty = document.createElement('div');
                empty.className = 'tab-empty-state';
                empty.innerHTML = '<p>No staged changes. Forge a card in the Cards tab to add it to the Assembly Line.</p>';
                list.appendChild(empty);
            }
        })
        .catch(function () {});
    }

    function _appendForgeLog(logEl, cardName, type, message) {
        if (!logEl) return;
        var entry = document.createElement('div');
        entry.className = 'forge-deck-log-entry forge-deck-log-entry--' + type;
        var icon = type === 'error' ? '\u2717' : '\u26a0';
        entry.textContent = icon + ' ' + cardName + ': ' + message;
        logEl.appendChild(entry);
        logEl.scrollTop = logEl.scrollHeight;
    }

    function onForgeDeckClick() {
        var btn             = $id('forge-deck-btn');
        var progressSection = $id('forge-deck-progress-section');
        var progressBar     = $id('forge-deck-progress-bar');
        var progressLabel   = $id('forge-deck-progress-label');
        var logEl           = $id('forge-deck-log');

        if (btn) btn.disabled = true;
        if (progressSection) progressSection.style.display = '';
        if (progressBar) progressBar.style.width = '0%';
        if (logEl) logEl.innerHTML = '';
        if (progressLabel) progressLabel.textContent = 'Fetching card list\u2026';

        fetch('/deck/' + encodeURIComponent(_deckName) + '/forge-all-list')
            .then(function (r) { return r.json(); })
            .then(function (listData) {
                if (listData.error) {
                    if (progressLabel) progressLabel.textContent = 'Error: ' + listData.error;
                    if (btn) btn.disabled = false;
                    return;
                }

                var cards = listData.cards || [];
                var total = cards.length;

                if (total === 0) {
                    if (progressLabel) progressLabel.textContent = 'No custom cards to forge.';
                    if (btn) btn.disabled = false;
                    return;
                }

                if (progressLabel) progressLabel.textContent = '0 / ' + total;

                var idx = 0;

                function forgeNext() {
                    if (idx >= total) {
                        if (progressBar) progressBar.style.width = '100%';
                        if (progressLabel) progressLabel.textContent = total + ' / ' + total + ' \u2014 Done';
                        if (btn) btn.disabled = false;
                        return;
                    }

                    var cardName = cards[idx];
                    idx++;

                    fetch(
                        '/deck/' + encodeURIComponent(_deckName) + '/forge-one?card=' + encodeURIComponent(cardName),
                        { method: 'POST' }
                    )
                        .then(function (r) { return r.json(); })
                        .then(function (result) {
                            var pct = Math.round(idx / total * 100);
                            if (progressBar) progressBar.style.width = pct + '%';
                            if (progressLabel) progressLabel.textContent = idx + ' / ' + total;

                            if (result.error) {
                                _appendForgeLog(logEl, cardName, 'error', result.error);
                            } else if (result.missing_artwork) {
                                _appendForgeLog(logEl, cardName, 'warning', 'No artwork image found');
                            }

                            if (result.staged_count !== undefined) {
                                _updatePublishBar(result.staged_count);
                            }

                            forgeNext();
                        })
                        .catch(function () {
                            _appendForgeLog(logEl, cardName, 'error', 'Network error');
                            forgeNext();
                        });
                }

                forgeNext();
            })
            .catch(function () {
                if (progressLabel) progressLabel.textContent = 'Failed to fetch card list \u2014 check server log';
                if (btn) btn.disabled = false;
            });
    }

    // ── Cockatrice Cleanup Dialog ─────────────────────────────────────────────

    var _ccScope    = 'all';   // 'all' or current deck folder name
    var _ccItems    = [];      // [{id, type, xml_name?, set_code?, category?, filename?}]
    var _ccSelected = new Set();

    function _ccEsc(str) {
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function onCockatriceCleanupClick() {
        var dialog = $id('cc-dialog');
        if (!dialog) return;

        _ccScope = 'all';
        _ccItems = [];
        _ccSelected.clear();

        var scopeAllBtn  = $id('cc-scope-all-btn');
        var scopeThisBtn = $id('cc-scope-this-btn');
        if (scopeAllBtn)  scopeAllBtn.classList.add('active');
        if (scopeThisBtn) scopeThisBtn.classList.remove('active');

        var resultsSection = $id('cc-results-section');
        if (resultsSection) resultsSection.style.display = 'none';

        var resultMsg = $id('cc-result-msg');
        if (resultMsg) { resultMsg.style.display = 'none'; resultMsg.innerHTML = ''; }

        var purgeBtn = $id('cc-purge-btn');
        if (purgeBtn) purgeBtn.disabled = true;

        var searchBtn = $id('cc-search-btn');
        if (searchBtn) searchBtn.disabled = false;

        dialog.showModal();
    }

    function _ccSearch() {
        var searchBtn      = $id('cc-search-btn');
        var resultsList    = $id('cc-results-list');
        var resultsSection = $id('cc-results-section');
        var resultMsg      = $id('cc-result-msg');

        if (searchBtn) searchBtn.disabled = true;
        if (resultMsg) { resultMsg.style.display = 'none'; resultMsg.innerHTML = ''; }
        if (resultsSection) resultsSection.style.display = '';
        if (resultsList) resultsList.innerHTML = '<div class="print-run-loading">Searching\u2026</div>';

        var scopeParam = (_ccScope === 'all') ? 'all' : encodeURIComponent(_deckName);
        fetch('/api/cockatrice-cleanup/scan?scope=' + scopeParam)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (searchBtn) searchBtn.disabled = false;
                if (data.error) {
                    if (resultsList) resultsList.innerHTML = '<div class="print-run-empty">Error: ' + _ccEsc(data.error) + '</div>';
                    return;
                }
                _ccItems = [];
                _ccSelected.clear();

                var xmlCards = data.junk_xml_cards || [];
                var images   = data.junk_images    || [];

                for (var i = 0; i < xmlCards.length; i++) {
                    var xc = xmlCards[i];
                    var xid = 'xml:' + xc.xml_name + '\x1f' + xc.set_code;
                    _ccItems.push({ id: xid, type: 'xml_card', xml_name: xc.xml_name, set_code: xc.set_code, category: xc.category });
                    _ccSelected.add(xid);
                }
                for (var j = 0; j < images.length; j++) {
                    var img = images[j];
                    var iid = 'img:' + img.filename;
                    _ccItems.push({ id: iid, type: 'image', filename: img.filename });
                    _ccSelected.add(iid);
                }

                _ccRenderList();
                _ccUpdateSelectedCount();
            })
            .catch(function () {
                if (searchBtn) searchBtn.disabled = false;
                if (resultsList) resultsList.innerHTML = '<div class="print-run-empty">Network error \u2014 check server.</div>';
            });
    }

    function _ccRenderList() {
        var listEl = $id('cc-results-list');
        if (!listEl) return;

        if (_ccItems.length === 0) {
            listEl.innerHTML = '<div class="print-run-empty">\u2705 No junk found \u2014 everything looks clean!</div>';
            var purgeBtn = $id('cc-purge-btn');
            if (purgeBtn) purgeBtn.disabled = true;
            return;
        }

        var xmlCards = _ccItems.filter(function (it) { return it.type === 'xml_card'; });
        var images   = _ccItems.filter(function (it) { return it.type === 'image'; });

        var html = '';

        if (xmlCards.length > 0) {
            html += '<div class="cc-group-header">XML Card Entries (' + xmlCards.length + ')</div>';
            for (var i = 0; i < xmlCards.length; i++) {
                var it = xmlCards[i];
                var sel = _ccSelected.has(it.id);
                var catLabel = it.category === 'orphan'
                    ? 'Orphaned from ' + _ccEsc(it.set_code) + ' (not in deck JSON)'
                    : 'Straggler \u2014 set ' + _ccEsc(it.set_code) + ' not in any deck';
                html += '<div class="cc-item-row' + (sel ? ' cc-item-selected' : '') + '">';
                html += '<button class="cc-check-btn pr-btn pr-btn-check' + (sel ? ' pr-btn-active' : '') + '" data-id="' + _ccEsc(it.id) + '">\u2713</button>';
                html += '<div class="cc-item-info">';
                html += '<span class="cc-item-name">' + _ccEsc(it.xml_name) + '</span>';
                html += '<span class="cc-item-meta">' + catLabel + '</span>';
                html += '</div>';
                html += '</div>';
            }
        }

        if (images.length > 0) {
            html += '<div class="cc-group-header">Orphaned Image Files (' + images.length + ')</div>';
            for (var k = 0; k < images.length; k++) {
                var img = images[k];
                var imgSel = _ccSelected.has(img.id);
                html += '<div class="cc-item-row' + (imgSel ? ' cc-item-selected' : '') + '">';
                html += '<button class="cc-check-btn pr-btn pr-btn-check' + (imgSel ? ' pr-btn-active' : '') + '" data-id="' + _ccEsc(img.id) + '">\u2713</button>';
                html += '<div class="cc-item-info">';
                html += '<span class="cc-item-name">' + _ccEsc(img.filename) + '</span>';
                html += '<span class="cc-item-meta">No matching card in any deck</span>';
                html += '</div>';
                html += '</div>';
            }
        }

        listEl.innerHTML = html;

        listEl.querySelectorAll('.cc-check-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                var id = this.dataset.id;
                if (_ccSelected.has(id)) _ccSelected.delete(id);
                else _ccSelected.add(id);
                _ccRenderList();
                _ccUpdateSelectedCount();
            });
        });
    }

    function _ccUpdateSelectedCount() {
        var el = $id('cc-selected-count');
        if (el) el.textContent = _ccSelected.size + ' selected';
        var purgeBtn = $id('cc-purge-btn');
        if (purgeBtn) purgeBtn.disabled = (_ccSelected.size === 0);
    }

    function _ccPurge() {
        var purgeBtn  = $id('cc-purge-btn');
        var cancelBtn = $id('cc-cancel-btn');
        var resultMsg = $id('cc-result-msg');

        if (purgeBtn)  purgeBtn.disabled  = true;
        if (cancelBtn) cancelBtn.disabled = true;

        var xmlCards = [];
        var images   = [];
        _ccSelected.forEach(function (id) {
            if (id.indexOf('xml:') === 0) {
                var rest = id.slice(4);
                var sep  = rest.indexOf('\x1f');
                if (sep >= 0) {
                    xmlCards.push({ xml_name: rest.slice(0, sep), set_code: rest.slice(sep + 1) });
                }
            } else if (id.indexOf('img:') === 0) {
                images.push(id.slice(4));
            }
        });

        fetch('/api/cockatrice-cleanup/purge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ xml_cards: xmlCards, images: images }),
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (cancelBtn) cancelBtn.disabled = false;
                if (!resultMsg) return;
                resultMsg.style.display = '';
                if (data.error) {
                    resultMsg.className = 'print-run-result print-run-result-err';
                    resultMsg.textContent = 'Error: ' + data.error;
                    if (purgeBtn) purgeBtn.disabled = (_ccSelected.size === 0);
                    return;
                }
                var xmlN  = data.xml_cards_removed || 0;
                var imgN  = data.images_deleted    || 0;
                var errs  = data.errors || [];
                resultMsg.className = 'print-run-result ' + (errs.length ? 'print-run-result-err' : 'print-run-result-ok');
                resultMsg.innerHTML =
                    (errs.length ? '\u26a0\ufe0f' : '\u2705') +
                    ' Removed ' + xmlN + ' XML entr' + (xmlN === 1 ? 'y' : 'ies') +
                    ' and deleted ' + imgN + ' image' + (imgN === 1 ? '' : 's') + '.' +
                    (errs.length ? '<pre class="pr-errors">' + _ccEsc(errs.join('\n')) + '</pre>' : '');
                _ccSelected.clear();
                _ccItems = [];
                var resultsSection = $id('cc-results-section');
                if (resultsSection) resultsSection.style.display = 'none';
            })
            .catch(function () {
                if (cancelBtn) cancelBtn.disabled = false;
                if (purgeBtn)  purgeBtn.disabled  = (_ccSelected.size === 0);
                if (resultMsg) {
                    resultMsg.style.display = '';
                    resultMsg.className = 'print-run-result print-run-result-err';
                    resultMsg.textContent = 'Network error \u2014 check the server.';
                }
            });
    }

    // ── Print Run Dialog ──────────────────────────────────────────────────────

    var _prScope    = 'all';   // 'all' or deck folder name
    var _prCards    = [];      // [{deck_name, card_name, modified_timestamp, modified_relative}]
    var _prSelected = new Set(); // keys of form "deck_name\x1fcard_name"

    function _prKey(card) { return card.deck_name + '\x1f' + card.card_name; }

    function _prEsc(str) {
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function onPreparePrintRunClick() {
        var dialog = $id('print-run-dialog');
        if (!dialog) return;

        _prSelected.clear();
        _prScope = 'all';

        var scopeAllBtn  = $id('pr-scope-all-btn');
        var scopeThisBtn = $id('pr-scope-this-btn');
        if (scopeAllBtn)  scopeAllBtn.classList.add('active');
        if (scopeThisBtn) scopeThisBtn.classList.remove('active');

        var resultEl = $id('pr-result');
        if (resultEl) { resultEl.style.display = 'none'; resultEl.innerHTML = ''; }

        _prUpdateSelectedCount();
        dialog.showModal();
        _prLoadCards();
    }

    function _prLoadCards() {
        var listEl = $id('print-run-card-list');
        if (listEl) listEl.innerHTML = '<div class="print-run-loading">Loading\u2026</div>';

        var scopeParam = (_prScope === 'all') ? 'all' : encodeURIComponent(_deckName);
        fetch('/api/print-run/cards?scope=' + scopeParam)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                _prCards = data.cards || [];
                _prRenderCardList();
            })
            .catch(function () {
                if (listEl) listEl.innerHTML = '<div class="print-run-loading">Error loading cards.</div>';
            });
    }

    function _prRenderCardList() {
        var listEl = $id('print-run-card-list');
        if (!listEl) return;

        if (_prCards.length === 0) {
            listEl.innerHTML = '<div class="print-run-empty">No cards published in the last 6 months.</div>';
            return;
        }

        var html = '';
        for (var i = 0; i < _prCards.length; i++) {
            var card = _prCards[i];
            var key  = _prKey(card);
            var sel  = _prSelected.has(key);
            html += '<div class="pr-card-row' + (sel ? ' pr-card-selected' : '') + '" data-idx="' + i + '">';
            html += '<div class="pr-card-info">';
            html += '<span class="pr-card-deck">' + _prEsc(card.deck_name) + '</span>';
            html += '<span class="pr-card-name">' + _prEsc(card.card_name) + '</span>';
            html += '</div>';
            html += '<span class="pr-card-time">' + _prEsc(card.modified_relative) + '</span>';
            html += '<div class="pr-card-btns">';
            html += '<button class="pr-btn pr-btn-check' + (sel ? ' pr-btn-active' : '') + '" data-idx="' + i + '" title="Select this card">\u2713</button>';
            html += '<button class="pr-btn pr-btn-upto" data-idx="' + i + '" title="Select this card and all more recent">\u2191</button>';
            html += '</div>';
            html += '</div>';
        }
        listEl.innerHTML = html;

        listEl.querySelectorAll('.pr-btn-check').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                var idx = parseInt(this.dataset.idx, 10);
                var key = _prKey(_prCards[idx]);
                if (_prSelected.has(key)) _prSelected.delete(key);
                else _prSelected.add(key);
                _prRenderCardList();
                _prUpdateSelectedCount();
            });
        });

        listEl.querySelectorAll('.pr-btn-upto').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                var idx = parseInt(this.dataset.idx, 10);
                // Select this card plus everything above it (more recent)
                for (var j = 0; j <= idx; j++) {
                    _prSelected.add(_prKey(_prCards[j]));
                }
                _prRenderCardList();
                _prUpdateSelectedCount();
            });
        });
    }

    function _prUpdateSelectedCount() {
        var el = $id('pr-selected-count');
        if (el) el.textContent = _prSelected.size + ' selected';
        var confirmBtn = $id('pr-confirm-btn');
        if (confirmBtn) confirmBtn.disabled = (_prSelected.size === 0);
    }

    function _prBuildPayload() {
        var byDeck = {};
        _prSelected.forEach(function (key) {
            var parts    = key.split('\x1f');
            var deckName = parts[0];
            var cardName = parts[1];
            if (!byDeck[deckName]) byDeck[deckName] = [];
            byDeck[deckName].push(cardName);
        });
        return byDeck;
    }

    function onPreparePrintRunConfirm() {
        var confirmBtn = $id('pr-confirm-btn');
        var cancelBtn  = $id('pr-cancel-btn');
        var resultEl   = $id('pr-result');
        if (confirmBtn) confirmBtn.disabled = true;
        if (cancelBtn)  cancelBtn.disabled  = true;

        fetch('/api/print-run/prepare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cards: _prBuildPayload() }),
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (cancelBtn) cancelBtn.disabled = false;
                if (!resultEl) return;
                resultEl.style.display = '';
                if (data.error) {
                    resultEl.className = 'print-run-result print-run-result-err';
                    resultEl.textContent = 'Error: ' + data.error;
                    if (confirmBtn) confirmBtn.disabled = false;
                    return;
                }
                var errLines = (data.errors || []).map(function (e) { return '\u2022 ' + e; }).join('\n');
                resultEl.className = 'print-run-result print-run-result-ok';
                resultEl.innerHTML =
                    '\u2705 Created <strong>' + _prEsc(data.output_dir) + '</strong> &mdash; ' +
                    data.copied + ' of ' + data.total_selected + ' image(s) copied.' +
                    (errLines ? '<pre class="pr-errors">' + _prEsc(errLines) + '</pre>' : '');
                if (confirmBtn) { confirmBtn.disabled = true; }
                _prSelected.clear();
                _prUpdateSelectedCount();
            })
            .catch(function () {
                if (cancelBtn) cancelBtn.disabled = false;
                if (confirmBtn) confirmBtn.disabled = false;
                if (resultEl) {
                    resultEl.style.display = '';
                    resultEl.className = 'print-run-result print-run-result-err';
                    resultEl.textContent = 'Network error \u2014 check the server.';
                }
            });
    }

    function onPublishAssemblyClick() {
        var dialog = $id('publish-confirm-dialog');
        var countEl = $id('confirm-staged-count');
        if (countEl) countEl.textContent = _stagedCount;
        if (dialog) dialog.showModal();
    }

    function doPublishAssembly() {
        var dialog     = $id('publish-confirm-dialog');
        var publishBtn = $id('publish-assembly-btn');
        var confirmBtn = $id('confirm-publish-btn');
        var logEl      = $id('assembly-publish-log');
        if (dialog)     dialog.close();
        if (publishBtn) publishBtn.disabled = true;
        if (confirmBtn) confirmBtn.disabled = true;
        if (logEl)      { logEl.innerHTML = ''; logEl.style.display = 'none'; }

        fetch('/deck/' + encodeURIComponent(_deckName) + '/publish-assembly-line', { method: 'POST' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (confirmBtn) confirmBtn.disabled = false;
                if (data.error) {
                    _showToast('Publish failed: ' + data.error, 'error');
                    if (publishBtn) publishBtn.disabled = (_stagedCount === 0);
                    return;
                }

                _updatePublishBar(0);

                var hasErrors = (data.printing_ok === false) || (data.cockatrice_ok === false);

                // Show publish log
                if (logEl) {
                    var entries = [];
                    entries.push({ ok: true,  text: data.cards_updated + ' card image' + (data.cards_updated !== 1 ? 's' : '') + ' updated in Cards/' });
                    if (data.printing_ok) {
                        entries.push({ ok: true, text: 'Printing images regenerated' });
                    } else {
                        entries.push({ ok: false, text: 'Some printing images failed' });
                        if (data.printing_errors && data.printing_errors.length) {
                            data.printing_errors.forEach(function(msg) {
                                entries.push({ ok: false, text: '\u00a0\u00a0' + msg, small: true });
                            });
                        }
                    }
                    if (data.cockatrice_ok === true)  entries.push({ ok: true,  text: 'Cockatrice export complete' });
                    if (data.cockatrice_ok === false) {
                        entries.push({ ok: false, text: 'Cockatrice export failed' });
                        if (data.cockatrice_error) entries.push({ ok: false, text: '\u00a0\u00a0' + data.cockatrice_error, small: true });
                    }
                    if (data.cockatrice_ok === null)  entries.push({ ok: null,  text: 'Cockatrice not configured \u2014 skipped' });
                    if (hasErrors) {
                        entries.push({ ok: null, text: 'Card images were saved. Reload when ready.' });
                    } else {
                        entries.push({ ok: null, text: 'Refreshing\u2026' });
                    }
                    logEl.innerHTML = entries.map(function(e) {
                        var cls = e.ok === true ? 'publish-log-ok' : e.ok === false ? 'publish-log-err' : 'publish-log-skip';
                        var icon = e.ok === true ? '\u2713' : e.ok === false ? '\u2717' : '\u2014';
                        var style = e.small ? ' style="font-size:0.85em;word-break:break-all;"' : '';
                        return '<div class="publish-log-entry ' + cls + '"' + style + '>' + icon + ' ' + e.text + '</div>';
                    }).join('');
                    if (hasErrors) {
                        logEl.innerHTML += '<button class="publish-log-reload-btn" onclick="window.location.reload()">Reload page</button>';
                    }
                    logEl.style.display = '';
                }

                if (!hasErrors) {
                    // Reload so Cards/Tokens galleries reflect all published changes
                    setTimeout(function () { window.location.reload(); }, 1200);
                } else if (publishBtn) {
                    publishBtn.disabled = false;
                }
            })
            .catch(function () {
                if (confirmBtn) confirmBtn.disabled = false;
                _showToast('Publish error \u2014 check server log', 'error');
                if (publishBtn) publishBtn.disabled = (_stagedCount === 0);
            });
    }

    function _showToast(message, type) {
        var toast = document.createElement('div');
        toast.className = 'manufactor-toast manufactor-toast--' + (type || 'info');
        toast.textContent = message;
        document.body.appendChild(toast);
        requestAnimationFrame(function () { toast.classList.add('manufactor-toast--visible'); });
        setTimeout(function () {
            toast.classList.remove('manufactor-toast--visible');
            setTimeout(function () { toast.remove(); }, 400);
        }, 5000);
    }

    // ── Opening Hand ──────────────────────────────────────────────────────────

    function _buildDeckPool() {
        var pool  = [];
        var items = document.querySelectorAll('#cards-tab-main .card-gallery .card-gallery-item[data-card-name]');
        items.forEach(function (item) {
            var name = item.dataset.cardName;
            if (_commanderNames.indexOf(name) !== -1) return;
            var qty = parseInt(item.dataset.quantity, 10) || 1;
            var img = item.querySelector('img.card-image');
            var src = img ? img.getAttribute('src') : '';
            for (var i = 0; i < qty; i++) {
                pool.push({ name: name, src: src });
            }
        });
        return pool;
    }

    function _shufflePool(arr) {
        var a = arr.slice();
        for (var i = a.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var t = a[i]; a[i] = a[j]; a[j] = t;
        }
        return a;
    }

    function _makeOhCard(card) {
        var div = document.createElement('div');
        div.className = 'oh-card';
        if (card.src) {
            var img = document.createElement('img');
            img.src = card.src;
            img.alt = card.name;
            img.className = 'oh-card-img';
            div.appendChild(img);
        } else {
            var span = document.createElement('span');
            span.textContent = card.name;
            div.appendChild(span);
            div.classList.add('oh-card--placeholder');
        }
        return div;
    }

    function _updateOhUi() {
        var drawBtn  = $id('oh-draw-btn');
        var statusEl = $id('oh-draw-status');
        var drawnRow = $id('oh-drawn-row');
        var canDraw  = _ohDrawnCount < 7 && _ohPosition < _ohPool.length;
        if (drawBtn)  drawBtn.disabled = !canDraw;
        if (statusEl) {
            statusEl.textContent = _ohDrawnCount > 0
                ? (_ohDrawnCount + '\u202f/\u202f7 extra card' + (_ohDrawnCount !== 1 ? 's' : '') + ' drawn')
                : '';
        }
        if (drawnRow) drawnRow.style.display = _ohDrawnCount > 0 ? '' : 'none';
    }

    function initOpeningHand() {
        _ohPool        = _shufflePool(_buildDeckPool());
        _ohPosition    = Math.min(7, _ohPool.length);
        _ohDrawnCount  = 0;
        _ohInitialized = true;

        var handRow  = $id('oh-hand-row');
        var drawnRow = $id('oh-drawn-row');
        if (!handRow) return;

        handRow.innerHTML  = '';
        drawnRow.innerHTML = '';

        for (var i = 0; i < _ohPosition; i++) {
            handRow.appendChild(_makeOhCard(_ohPool[i]));
        }
        _updateOhUi();
    }

    function _ohDraw() {
        if (_ohDrawnCount >= 7 || _ohPosition >= _ohPool.length) return;
        var card     = _ohPool[_ohPosition++];
        _ohDrawnCount++;
        var drawnRow = $id('oh-drawn-row');
        if (drawnRow) drawnRow.appendChild(_makeOhCard(card));
        _updateOhUi();
    }

    function _ohInitOnFirstSwitch() {
        if (!_ohInitialized) initOpeningHand();
    }

    // ── Bootstrap ─────────────────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', function () {
        var tabsEl = document.querySelector('.deck-tabs');
        if (!tabsEl) return;   // Not a deck page — skip

        // Deck name from URL: /deck/<name>
        var parts = window.location.pathname.split('/');
        _deckName       = parts[2] ? decodeURIComponent(parts[2]) : '';
        _stagedCount    = parseInt(tabsEl.dataset.stagedCount || '0', 10);
        try { _commanderNames = JSON.parse(tabsEl.dataset.commanderNames || '[]'); } catch (e) { _commanderNames = []; }

        // Tab buttons
        tabsEl.querySelectorAll('.deck-tab').forEach(function (btn) {
            btn.addEventListener('click', function () { switchTab(btn.dataset.tab, true); });
        });

        // Card clicks (delegated so grouped / cloned items also fire)
        document.body.addEventListener('click', function (e) {
            // Flip button — must check before card-gallery-item to stop propagation
            var flipBtn = e.target.closest('.card-flip-btn');
            if (flipBtn) { e.preventDefault(); e.stopPropagation(); _handleGalleryFlip(flipBtn); return; }
            var item = e.target.closest('.card-gallery-item[data-card-name]');
            if (item) { e.preventDefault(); openCardEditor(item.dataset.cardName); return; }
            var cmd = e.target.closest('[data-commander-name]');
            if (cmd) { e.preventDefault(); switchTab('cards', false); openCardEditor(cmd.dataset.commanderName); }
        });

        // Back button
        var backBtn = $id('editor-back-btn');
        if (backBtn) backBtn.addEventListener('click', function () { closeCardEditor(true); });

        // Face tabs
        document.querySelectorAll('.editor-face-tab').forEach(function (btn) {
            btn.addEventListener('click', function () { switchFace(btn.dataset.face); });
        });

        // Mode toggle
        document.querySelectorAll('.editor-mode-btn').forEach(function (btn) {
            btn.addEventListener('click', function () { switchEditorMode(btn.dataset.mode); });
        });

        // Form field change detection
        ['ef-name', 'ef-mana', 'ef-cardtype', 'ef-subtype', 'ef-rules',
         'ef-power', 'ef-toughness', 'ef-rarity', 'ef-flavor',
         'ef-legendary', 'ef-basic', 'ef-snow',
         'ef-artist', 'ef-frame', 'ef-dfc-type', 'ef-quantity',
         'ef-ss-name', 'ef-ss-mana', 'ef-ss-cardtype', 'ef-ss-subtype', 'ef-ss-rules'].forEach(function (id) {
            var el = $id(id);
            if (!el) return;
            el.addEventListener('input', onFormChange);
            el.addEventListener('change', onFormChange);
        });

        // Card type → may switch rules mode
        ['ef-cardtype', 'ef-subtype'].forEach(function (id) {
            var el = $id(id);
            if (!el) return;
            el.addEventListener('input',  _onCardTypeChange);
            el.addEventListener('change', _onCardTypeChange);
        });

        // Add Section button
        var addSectionBtn = $id('ef-add-section-btn');
        if (addSectionBtn) addSectionBtn.addEventListener('click', function () { _addSection(); });

        // Remove Section — event delegation on container
        var sectionsContainer = $id('ef-sections-container');
        if (sectionsContainer) {
            sectionsContainer.addEventListener('click', function (e) {
                if (!e.target.classList.contains('ef-section-remove-btn')) return;
                var rows = sectionsContainer.querySelectorAll('.ef-section-row');
                if (rows.length <= 1) return;
                e.target.closest('.ef-section-row').remove();
                _renumberSections();
                _markSectionChange();
            });
        }

        // Add / Remove Subspell buttons
        var addSubspellBtn = $id('add-subspell-btn');
        if (addSubspellBtn) addSubspellBtn.addEventListener('click', function () {
            _setSubspellActive(true);
            onFormChange();
        });
        var removeSubspellBtn = $id('remove-subspell-btn');
        if (removeSubspellBtn) removeSubspellBtn.addEventListener('click', function () {
            _SS_FIELDS.forEach(function (k) { setVal('ef-ss-' + k, ''); });
            _setSubspellActive(false);
            onFormChange();
        });

        // Populate card frames datalist
        var framesDatalist = $id('card-frames-list');
        if (framesDatalist) {
            fetch('/card-frames')
                .then(function (r) { return r.json(); })
                .then(function (files) {
                    files.forEach(function (f) {
                        var opt = document.createElement('option');
                        opt.value = f;
                        framesDatalist.appendChild(opt);
                    });
                })
                .catch(function () { /* silently ignore */ });
        }

        // Tag add button + picker
        var tagAddBtn = $id('tag-add-btn');
        if (tagAddBtn) tagAddBtn.addEventListener('click', openTagPicker);
        var tagInput = $id('tag-picker-input');
        if (tagInput) {
            tagInput.addEventListener('input', function () { renderTagOptions(tagInput.value); });
            tagInput.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') { closeTagPicker(); return; }
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var val = tagInput.value.trim();
                    if (!val) return;
                    // If there's exactly one visible option, use it; else create new
                    var visible = $id('tag-picker-options').querySelectorAll('.tag-picker-option:not(.tag-picker-option--new)');
                    if (visible.length === 1 && visible[0].textContent.toLowerCase() === val.toLowerCase()) {
                        doAddTag(visible[0].textContent);
                    } else {
                        doAddTag(val);
                    }
                }
            });
        }
        // Close picker when clicking outside
        document.addEventListener('click', function (e) {
            var picker = $id('tag-picker');
            var btn    = $id('tag-add-btn');
            if (picker && picker.style.display !== 'none') {
                if (!picker.contains(e.target) && e.target !== btn) {
                    closeTagPicker();
                }
            }
        });

        // Set As Commander button
        var setCmdBtn = $id('set-commander-btn');
        if (setCmdBtn) setCmdBtn.addEventListener('click', function () {
            if (!_currentCardName) return;
            if (Date.now() - _editorOpenedAt < 400) return;
            fetch('/deck/' + encodeURIComponent(_deckName) + '/toggle-commander', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ card_name: _currentCardName })
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) { alert('Error: ' + data.error); return; }
                _commanderNames = data.commanders;
                _updateCommanderBtn(_currentCardName);
                // Reload so the commander section in the deck header reflects the change
                // Strip hash so the editor doesn't auto-reopen after reload
                window.location.replace(window.location.pathname + window.location.search);
            })
            .catch(function () { alert('Failed to update commander status.'); });
        });

        // Delete Card button
        var deleteCardBtn = $id('delete-card-btn');
        if (deleteCardBtn) deleteCardBtn.addEventListener('click', function () {
            if (!_currentCardName) return;
            if (!confirm('Stage "' + _currentCardName + '" for deletion?\n\nThe card will be removed from the deck when you publish the Assembly Line.')) return;
            fetch('/deck/' + encodeURIComponent(_deckName) + '/stage-delete?name=' + encodeURIComponent(_currentCardName), {
                method: 'POST'
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) { alert('Error: ' + data.error); return; }
                _updatePublishBar(data.staged_count);
                closeCardEditor(true);
                switchTab('assembly', true);
            })
            .catch(function (err) { alert('Failed to stage deletion: ' + err); });
        });

        // Forge button
        var forgeBtn = $id('forge-btn');
        if (forgeBtn) forgeBtn.addEventListener('click', onForgeClick);

        // Create Card button
        var createCardBtn = $id('create-card-btn');
        if (createCardBtn) createCardBtn.addEventListener('click', openNewCardEditor);

        // Add Real Card button
        var addRealCardBtn = $id('add-real-card-btn');
        if (addRealCardBtn) addRealCardBtn.addEventListener('click', openRealCardDialogAdd);

        // ── Real Card Dialog wiring ───────────────────────────────────────────
        (function () {
            var rcdDialog = $id('real-card-dialog');
            if (!rcdDialog) return;

            // Close button
            var closeBtn = $id('rcd-close-btn');
            if (closeBtn) closeBtn.addEventListener('click', function () { rcdDialog.close(); });

            // Close on backdrop click
            rcdDialog.addEventListener('click', function (e) {
                if (e.target === rcdDialog) rcdDialog.close();
            });

            // Search input — debounced
            var searchInput = $id('rcd-search-input');
            if (searchInput) {
                searchInput.addEventListener('input', function () {
                    clearTimeout(_rcdSearchTimer);
                    _rcdSearchTimer = setTimeout(_rcdDoSearch, 350);
                });
                searchInput.addEventListener('keydown', function (e) {
                    if (e.key === 'Escape') {
                        $id('rcd-search-results').style.display = 'none';
                        $id('rcd-search-status').style.display  = 'none';
                    }
                });
            }

            // Color filter checkboxes — re-trigger search on change
            ['w', 'u', 'b', 'r', 'g'].forEach(function (c) {
                var cb = $id('rcd-color-' + c);
                if (cb) cb.addEventListener('change', function () {
                    clearTimeout(_rcdSearchTimer);
                    _rcdSearchTimer = setTimeout(_rcdDoSearch, 150);
                });
            });

            // Add / Update button
            var addBtn = $id('rcd-add-btn');
            if (addBtn) addBtn.addEventListener('click', _rcdSubmit);

            // Delete button — reuse stage-delete endpoint
            var delBtn = $id('rcd-delete-btn');
            if (delBtn) delBtn.addEventListener('click', function () {
                var cardName = _rcdCardBeingEdited;
                if (!cardName) return;
                if (!confirm('Stage "' + cardName + '" for deletion?\n\nThe card will be removed when you publish the Assembly Line.')) return;
                fetch('/deck/' + encodeURIComponent(_deckName) + '/stage-delete?name=' + encodeURIComponent(cardName), { method: 'POST' })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.error) { _rcdShowStatus('error', 'Error: ' + data.error); return; }
                        _updatePublishBar(data.staged_count);
                        rcdDialog.close();
                        _markCanonicalItemStaged(cardName);
                    })
                    .catch(function () { _rcdShowStatus('error', 'Delete failed.'); });
            });
        }());

        // Opening Hand buttons
        var ohRestartBtn = $id('oh-restart-btn');
        if (ohRestartBtn) ohRestartBtn.addEventListener('click', initOpeningHand);
        var ohDrawBtn = $id('oh-draw-btn');
        if (ohDrawBtn) ohDrawBtn.addEventListener('click', _ohDraw);

        // Actions tab buttons
        var forgeDeckBtn = $id('forge-deck-btn');
        if (forgeDeckBtn) forgeDeckBtn.addEventListener('click', onForgeDeckClick);

        var cockatriceCleanupBtn = $id('cockatrice-cleanup-btn');
        if (cockatriceCleanupBtn) cockatriceCleanupBtn.addEventListener('click', onCockatriceCleanupClick);

        var preparePrintRunBtn = $id('prepare-print-run-btn');
        if (preparePrintRunBtn) preparePrintRunBtn.addEventListener('click', onPreparePrintRunClick);

        var editTagsBtn = $id('edit-tags-btn');
        if (editTagsBtn) editTagsBtn.addEventListener('click', openEditTagsDialog);

        var editTagsCloseBtn = $id('edit-tags-close-btn');
        if (editTagsCloseBtn) editTagsCloseBtn.addEventListener('click', function () {
            var dialog = $id('edit-tags-dialog');
            if (dialog) dialog.close();
        });

        // Print Run dialog wiring
        var prScopeAllBtn  = $id('pr-scope-all-btn');
        var prScopeThisBtn = $id('pr-scope-this-btn');
        var prConfirmBtn   = $id('pr-confirm-btn');
        var prCancelBtn    = $id('pr-cancel-btn');

        if (prScopeAllBtn) prScopeAllBtn.addEventListener('click', function () {
            _prScope = 'all';
            prScopeAllBtn.classList.add('active');
            if (prScopeThisBtn) prScopeThisBtn.classList.remove('active');
            _prSelected.clear();
            _prUpdateSelectedCount();
            _prLoadCards();
        });
        if (prScopeThisBtn) prScopeThisBtn.addEventListener('click', function () {
            _prScope = 'this';
            prScopeThisBtn.classList.add('active');
            if (prScopeAllBtn) prScopeAllBtn.classList.remove('active');
            _prSelected.clear();
            _prUpdateSelectedCount();
            _prLoadCards();
        });
        if (prConfirmBtn) prConfirmBtn.addEventListener('click', onPreparePrintRunConfirm);
        if (prCancelBtn)  prCancelBtn.addEventListener('click', function () {
            var dialog = $id('print-run-dialog');
            if (dialog) dialog.close();
        });

        // Cockatrice Cleanup dialog wiring
        var ccScopeAllBtn  = $id('cc-scope-all-btn');
        var ccScopeThisBtn = $id('cc-scope-this-btn');
        var ccSearchBtn    = $id('cc-search-btn');
        var ccPurgeBtn     = $id('cc-purge-btn');
        var ccCancelBtn    = $id('cc-cancel-btn');

        if (ccScopeAllBtn) ccScopeAllBtn.addEventListener('click', function () {
            _ccScope = 'all';
            ccScopeAllBtn.classList.add('active');
            if (ccScopeThisBtn) ccScopeThisBtn.classList.remove('active');
        });
        if (ccScopeThisBtn) ccScopeThisBtn.addEventListener('click', function () {
            _ccScope = _deckName;
            ccScopeThisBtn.classList.add('active');
            if (ccScopeAllBtn) ccScopeAllBtn.classList.remove('active');
        });
        if (ccSearchBtn) ccSearchBtn.addEventListener('click', _ccSearch);
        if (ccPurgeBtn)  ccPurgeBtn.addEventListener('click', _ccPurge);
        if (ccCancelBtn) ccCancelBtn.addEventListener('click', function () {
            var dialog = $id('cc-dialog');
            if (dialog) dialog.close();
        });

        // Assembly Line buttons
        var publishAssemblyBtn = $id('publish-assembly-btn');
        if (publishAssemblyBtn) publishAssemblyBtn.addEventListener('click', onPublishAssemblyClick);

        // Publish confirm dialog buttons
        var confirmPublishBtn = $id('confirm-publish-btn');
        if (confirmPublishBtn) confirmPublishBtn.addEventListener('click', doPublishAssembly);

        var confirmReviewBtn = $id('confirm-review-btn');
        if (confirmReviewBtn) confirmReviewBtn.addEventListener('click', function () {
            var dialog = $id('publish-confirm-dialog');
            if (dialog) dialog.close();
        });

        // Initial hash routing
        handleHash(window.location.hash);
        window.addEventListener('hashchange', function () { handleHash(window.location.hash); });

        // ── Deck metadata hammer-button editing ──────────────────────────
        (function () {
            var dialog    = $id('meta-edit-dialog');
            if (!dialog) return;

            var titleEl   = $id('meta-edit-title');
            var container = $id('meta-edit-field-container');
            var saveBtn   = $id('meta-edit-save-btn');
            var cancelBtn = $id('meta-edit-cancel-btn');
            var errorEl   = $id('meta-edit-error');
            var deckNameEncoded = dialog.dataset.deckName || '';
            var currentSetname  = dialog.dataset.currentSetname || 'UNK';

            var _currentField = null;

            var FIELD_CONFIG = {
                deck_name: {
                    title: 'Edit Deck Name',
                    build: function (current) {
                        var inp = document.createElement('input');
                        inp.type = 'text'; inp.id = 'meta-edit-input';
                        inp.value = current; inp.maxLength = 120;
                        return inp;
                    },
                    value: function () { return $id('meta-edit-input').value.trim(); },
                },
                format: {
                    title: 'Edit Format',
                    build: function (current) {
                        var sel = document.createElement('select');
                        sel.id = 'meta-edit-input';
                        ['Commander','Standard','Modern','Legacy','Vintage','Draft','Casual'].forEach(function (f) {
                            var opt = document.createElement('option');
                            opt.value = opt.textContent = f;
                            if (f === current) opt.selected = true;
                            sel.appendChild(opt);
                        });
                        return sel;
                    },
                    value: function () { return $id('meta-edit-input').value; },
                },
                setname: {
                    title: 'Edit Set Code',
                    build: function (current) {
                        var wrap = document.createElement('div');
                        wrap.style.display = 'flex'; wrap.style.flexDirection = 'column'; wrap.style.gap = '6px';
                        var inp = document.createElement('input');
                        inp.type = 'text'; inp.id = 'meta-edit-input';
                        inp.value = current; inp.maxLength = 3;
                        inp.style.textTransform = 'uppercase'; inp.style.width = '90px';
                        inp.addEventListener('input', function () { inp.value = inp.value.toUpperCase(); });
                        var hint = document.createElement('span');
                        hint.className = 'form-hint';
                        hint.textContent = '3-letter code used in Cockatrice. Changing this takes effect on next Publish.';
                        wrap.appendChild(inp); wrap.appendChild(hint);
                        return wrap;
                    },
                    value: function () { return $id('meta-edit-input').value.trim().toUpperCase(); },
                },
                description: {
                    title: 'Edit Description',
                    build: function (current) {
                        var ta = document.createElement('textarea');
                        ta.id = 'meta-edit-input'; ta.rows = 4;
                        ta.value = current; ta.placeholder = 'Describe your deck...';
                        return ta;
                    },
                    value: function () { return $id('meta-edit-input').value.trim(); },
                },
            };

            function getCurrentValue(field) {
                if (field === 'deck_name')   return ($id('deck-display-name')   || {}).textContent || '';
                if (field === 'format')      return ($id('deck-display-format') || {}).textContent || '';
                if (field === 'setname')     return currentSetname;
                if (field === 'description') return ($id('deck-display-description') || {}).textContent || '';
                return '';
            }

            function openMetaDialog(field) {
                var cfg = FIELD_CONFIG[field];
                if (!cfg) return;
                _currentField = field;
                titleEl.textContent = cfg.title;
                container.innerHTML = '';
                container.appendChild(cfg.build(getCurrentValue(field)));
                errorEl.style.display = 'none';
                dialog.showModal();
                var inp = $id('meta-edit-input');
                if (inp) { inp.focus(); if (inp.select) inp.select(); }
            }

            // Wire up all hammer buttons
            document.querySelectorAll('.hammer-btn[data-meta-field]').forEach(function (btn) {
                btn.addEventListener('click', function () { openMetaDialog(btn.dataset.metaField); });
            });

            cancelBtn.addEventListener('click', function () { dialog.close(); });
            dialog.addEventListener('click', function (e) {
                if (e.target === dialog) dialog.close();
            });

            saveBtn.addEventListener('click', function () {
                var cfg = FIELD_CONFIG[_currentField];
                if (!cfg) return;
                var val = cfg.value();
                if (!val && _currentField !== 'description') {
                    errorEl.textContent = 'Value cannot be empty.';
                    errorEl.style.display = 'block';
                    return;
                }
                if (_currentField === 'setname' && val.length !== 3) {
                    errorEl.textContent = 'Set code must be exactly 3 characters.';
                    errorEl.style.display = 'block';
                    return;
                }

                var payload = {};
                payload[_currentField] = val;

                saveBtn.disabled = true;
                fetch('/deck/' + deckNameEncoded + '/update-metadata', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    saveBtn.disabled = false;
                    if (data.error) {
                        errorEl.textContent = data.error;
                        errorEl.style.display = 'block';
                        return;
                    }
                    // Update displayed values in-page
                    if (_currentField === 'deck_name') {
                        var el = $id('deck-display-name');
                        if (el) el.textContent = val;
                        document.title = val + ' - Manufactor';
                    } else if (_currentField === 'format') {
                        var el = $id('deck-display-format');
                        if (el) el.textContent = val;
                    } else if (_currentField === 'setname') {
                        var el = $id('deck-display-setname');
                        if (el) el.textContent = 'Set: ' + val;
                        currentSetname = val;
                        dialog.dataset.currentSetname = val;
                    } else if (_currentField === 'description') {
                        var el = $id('deck-display-description');
                        if (el) {
                            el.textContent = val;
                            el.classList.toggle('deck-description-empty', !val);
                        }
                    }
                    dialog.close();
                })
                .catch(function () {
                    saveBtn.disabled = false;
                    errorEl.textContent = 'Save failed. Please try again.';
                    errorEl.style.display = 'block';
                });
            });

            // Save on Enter for single-line inputs
            dialog.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    saveBtn.click();
                }
            });
        }());

    });

}());
