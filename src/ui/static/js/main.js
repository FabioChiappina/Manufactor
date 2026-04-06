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

    // Apply filters
    const filteredItems = allItems.filter(function(item) {
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

    var totalCardCount = 0;
    var nonLandCount   = 0;
    var totalMV        = 0;

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

        totalCardCount += qty;

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
        nonLandCount += qty;
        totalMV      += mv * qty;

        if (!manaCurve[mv]) manaCurve[mv] = { permanents: 0, spells: 0 };

        // Classify as permanent if any permanent supertype present
        var isPermanent = isCreature || isArtifact || isEnchantment || isPlaneswalker || isBattle;
        if (isPermanent) {
            manaCurve[mv].permanents += qty;
        } else {
            manaCurve[mv].spells += qty;
        }
    });

    var mvStats = {
        totalMV:    totalMV,
        avgAll:     totalCardCount > 0 ? totalMV / totalCardCount : 0,
        avgNonLand: nonLandCount   > 0 ? totalMV / nonLandCount   : 0
    };

    if (manaCurveCanvas) _renderManaCurveChart(manaCurveCanvas, manaCurve, mvStats);
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

function _renderManaCurveChart(canvas, manaCurve, mvStats) {
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
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Cards may count in multiple bars', w / 2, h - 4);
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

    // ── Face data helpers ─────────────────────────────────────────────────────
    var _FACE_STR_FIELDS  = ['name', 'mana', 'cardtype', 'subtype', 'rules', 'power', 'toughness', 'flavor'];
    var _FACE_BOOL_FIELDS = ['legendary', 'basic', 'snow'];

    function buildFaceDict(faceData) {
        var f = faceData || {};
        var result = {};
        _FACE_STR_FIELDS.forEach(function (k)  { if (f[k]) result[k] = f[k]; });
        _FACE_BOOL_FIELDS.forEach(function (k) { if (f[k]) result[k] = 1; });
        return result;
    }

    function populateFaceForm(faceDict) {
        var f = faceDict || {};
        _FACE_STR_FIELDS.forEach(function (k)  { setVal('ef-' + k, f[k] || ''); });
        _FACE_BOOL_FIELDS.forEach(function (k) { setCheck('ef-' + k, f[k]); });
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
        ['cards', 'tokens', 'assembly'].forEach(function (key) {
            var pane = $id('tab-' + key);
            if (!pane) return;
            var show = (key === tabName);
            pane.style.display = show ? '' : 'none';
            pane.classList.toggle('tab-pane--active', show);
        });
        if (pushHash) history.replaceState(null, '', '#' + tabName);
        if (tabName === 'assembly') loadAssemblyLineData();
    }

    function handleHash(hash) {
        if (!hash || hash === '#' || hash === '#cards') { switchTab('cards', false); return; }
        if (hash === '#tokens')   { switchTab('tokens', false);   return; }
        if (hash === '#assembly') { switchTab('assembly', false); return; }
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

    // ── Open / Close Editor ───────────────────────────────────────────────────
    function openCardEditor(cardName) {
        _currentCardName = cardName;
        _isNewCard       = false;
        _editorIsDirty   = false;
        _currentFace     = 'front';
        _faceCache       = { front: {}, back: {} };
        _serverData      = null;

        $id('editor-card-title').textContent = cardName;
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
            })
            .catch(function () { setArtworkStatus('missing', 'Failed to load card'); });
    }

    function openNewCardEditor() {
        _currentCardName = null;
        _isNewCard       = true;
        _editorIsDirty   = true;
        _originalJson    = '';
        _currentFace     = 'front';
        _faceCache       = { front: {}, back: {} };
        _serverData      = null;

        $id('editor-card-title').textContent  = 'New Card';
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

        // Clear stale data so the next opened card doesn't briefly flash old content
        _currentTags = [];
        _deckTags    = [];
        renderTags();
        closeTagPicker();
        updatePreview(null);
        setArtworkStatus('', '');
        $id('editor-card-title').textContent = '';

        $id('card-editor-panel').style.display = 'none';
        $id('cards-tab-main').style.display    = '';

        if (updateHash !== false) history.replaceState(null, '', '#cards');
    }

    // ── Form Population ───────────────────────────────────────────────────────
    function populateForm(data) {
        var frontFace;
        if (data.front) {
            frontFace = buildFaceDict(data.front);
        } else {
            frontFace = buildFaceDict({
                name: data.name, mana: data.cost, cardtype: data.cardtype,
                subtype: data.subtype, rules: data.rules, power: data.power,
                toughness: data.toughness, flavor: data.flavor,
                legendary: data.legendary, basic: data.basic, snow: data.snow
            });
        }
        _faceCache   = { front: frontFace, back: buildFaceDict(data.back || {}) };
        _currentFace = 'front';
        var rarEl = $id('ef-rarity');
        if (rarEl) rarEl.value = (data.rarity || 'common').toLowerCase();
        var frameEl = $id('ef-frame');
        if (frameEl) frameEl.value = data.frame || '';
        var dfcEl = $id('ef-dfc-type');
        if (dfcEl) dfcEl.value = data.double_faced_type || '';
        var artistEl = $id('ef-artist');
        if (artistEl) artistEl.value = data.artist || '';
        populateFaceForm(frontFace);
        updateFaceTabs();
    }

    // ── Serialise form → card JSON ────────────────────────────────────────────
    function serializeForm() {
        _faceCache[_currentFace] = captureCurrentFace();
        var rarEl   = $id('ef-rarity');
        var frameEl = $id('ef-frame');
        var dfcEl   = $id('ef-dfc-type');
        var result = {
            front:    _faceCache.front,
            rarity:   rarEl ? rarEl.value : 'common',
            quantity: 1
        };
        if (_faceCache.back && Object.keys(_faceCache.back).length > 0) {
            result.back = _faceCache.back;
        }
        var dfcVal = dfcEl ? dfcEl.value : '';
        if (dfcVal) result.double_faced_type = dfcVal;
        var artistEl = $id('ef-artist');
        var artistVal = artistEl ? artistEl.value.trim() : '';
        if (artistVal) result.artist = artistVal;
        var frameVal = frameEl ? frameEl.value.trim() : '';
        if (frameVal) result.frame = frameVal;
        return result;
    }

    // Normalise server card dict into canonical shape for dirty comparison
    function normaliseCard(data) {
        var frontFace;
        if (data.front) {
            frontFace = buildFaceDict(data.front);
        } else {
            frontFace = buildFaceDict({
                name: data.name, mana: data.cost, cardtype: data.cardtype,
                subtype: data.subtype, rules: data.rules, power: data.power,
                toughness: data.toughness, flavor: data.flavor,
                legendary: data.legendary, basic: data.basic, snow: data.snow
            });
        }
        var result = { front: frontFace, rarity: (data.rarity || 'common').toLowerCase(), quantity: 1 };
        if (data.back) {
            var backFace = buildFaceDict(data.back);
            if (Object.keys(backFace).length > 0) result.back = backFace;
        }
        if (data.double_faced_type) result.double_faced_type = data.double_faced_type;
        if (data.artist) result.artist = data.artist;
        if (data.frame) result.frame = data.frame;
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
            forgeBtn.disabled = !active;
            forgeBtn.classList.toggle('btn-forge--active', active);
        }
        var closeForgeBtnEl = $id('close-forge-btn');
        if (closeForgeBtnEl) closeForgeBtnEl.disabled = !active;
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
            if (img) { img.src = base64; img.style.display = ''; }
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

    function onForgeClick(closeAfter) {
        var cardData = getEditorJson();
        if (!cardData) return;

        var url = '/deck/' + encodeURIComponent(_deckName) + '/forge-card?name='
            + encodeURIComponent(_currentCardName || '_new');

        // Disable forge buttons while request is in flight
        var forgeBtn        = $id('forge-btn');
        var closeForgeBtnEl = $id('close-forge-btn');
        if (forgeBtn)        forgeBtn.disabled        = true;
        if (closeForgeBtnEl) closeForgeBtnEl.disabled = true;
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
                updateButtonStates();
                return;
            }

            // Update card preview (respect current face tab)
            var previewB64 = (_currentFace === 'back' && data.back_image_base64)
                ? data.back_image_base64
                : data.image_base64;
            if (previewB64) updatePreview(previewB64);

            // Update assembly badge + publish bar count/button
            _updatePublishBar(data.staged_count || 0);

            // New card now exists in the deck — track its name
            if (_isNewCard && cardData.front && cardData.front.name) {
                _currentCardName = cardData.front.name;
                _isNewCard       = false;
            }

            _editorIsDirty = false;
            setArtworkStatus('found', 'Forged \u2713');
            updateButtonStates();

            // Mark the gallery item as staged
            if (_currentCardName) {
                var galItem = document.querySelector('.card-gallery-item[data-card-name="' + _currentCardName.replace(/"/g, '\\"') + '"]');
                if (galItem) {
                    galItem.dataset.staged = 'true';
                    var imgCon = galItem.querySelector('.card-image-container, .card-image-placeholder');
                    if (imgCon && !imgCon.querySelector('.staged-overlay')) {
                        var ov = document.createElement('div');
                        ov.className = 'staged-overlay';
                        ov.innerHTML = 'AWAITING<br>ASSEMBLY LINE';
                        imgCon.appendChild(ov);
                    }
                }
            }

            if (closeAfter) closeCardEditor(true);
        })
        .catch(function (err) {
            console.error('Forge error:', err);
            setArtworkStatus('missing', 'Forge error \u2014 check server log');
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
        label.className = 'assembly-card-label';
        label.textContent = item.card_name + (item.is_new ? ' (new)' : '');
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
            origPlaceholder.textContent = item.is_new ? 'New Card' : 'No Image';
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
        stgCaption.textContent = 'Staged';
        if (item.staged_image_base64) {
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
            // Update gallery item staged state
            var galItem = document.querySelector('.card-gallery-item[data-card-name="' + cardName.replace(/"/g, '\\"') + '"]');
            if (galItem) {
                galItem.dataset.staged = 'false';
                var ov = galItem.querySelector('.staged-overlay');
                if (ov) ov.remove();
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

    function onForgeAllClick() {
        var btn    = $id('forge-all-btn');
        var status = $id('forge-all-status');
        if (btn) btn.disabled = true;
        if (status) status.textContent = 'Forging\u2026';

        fetch('/deck/' + encodeURIComponent(_deckName) + '/forge-all', { method: 'POST' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (btn) btn.disabled = false;
                if (data.error) {
                    if (status) status.textContent = 'Error: ' + data.error;
                    return;
                }
                if (status) status.textContent = 'Forged ' + data.forged + ' card(s) \u2713';
                _updatePublishBar(data.staged_count || 0);
                loadAssemblyLineData();
            })
            .catch(function () {
                if (btn) btn.disabled = false;
                if (status) status.textContent = 'Forge error \u2014 check server log';
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
                loadAssemblyLineData();

                // Clear staged-overlay badges and update data-staged in gallery
                document.querySelectorAll('.card-gallery-item[data-staged="true"]').forEach(function (item) {
                    item.dataset.staged = 'false';
                    var ov = item.querySelector('.staged-overlay');
                    if (ov) ov.remove();
                });

                // Refresh card images in the gallery for each published card
                if (data.published_cards && data.published_cards.length) {
                    _refreshGalleryImages(data.published_cards);
                }

                // Show publish log
                if (logEl) {
                    var entries = [];
                    entries.push({ ok: true,  text: data.cards_updated + ' card image' + (data.cards_updated !== 1 ? 's' : '') + ' updated in Cards/' });
                    entries.push({ ok: data.printing_ok, text: data.printing_ok ? 'Printing images regenerated' : 'Some printing images failed — check server log' });
                    if (data.cockatrice_ok === true)  entries.push({ ok: true,  text: 'Cockatrice export complete' });
                    if (data.cockatrice_ok === false) entries.push({ ok: false, text: 'Cockatrice export failed — check server log' });
                    if (data.cockatrice_ok === null)  entries.push({ ok: null,  text: 'Cockatrice not configured — skipped' });
                    logEl.innerHTML = entries.map(function(e) {
                        var cls = e.ok === true ? 'publish-log-ok' : e.ok === false ? 'publish-log-err' : 'publish-log-skip';
                        var icon = e.ok === true ? '\u2713' : e.ok === false ? '\u2717' : '\u2014';
                        return '<div class="publish-log-entry ' + cls + '">' + icon + ' ' + e.text + '</div>';
                    }).join('');
                    logEl.style.display = '';
                }
            })
            .catch(function () {
                if (confirmBtn) confirmBtn.disabled = false;
                _showToast('Publish error \u2014 check server log', 'error');
                if (publishBtn) publishBtn.disabled = (_stagedCount === 0);
            });
    }

    function _refreshGalleryImages(cardNames) {
        cardNames.forEach(function (cardName) {
            fetch('/deck/' + encodeURIComponent(_deckName) + '/card-data?name=' + encodeURIComponent(cardName))
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (!data.image_base64) return;
                    var galItem = document.querySelector('.card-gallery-item[data-card-name="' + cardName.replace(/"/g, '\\"') + '"]');
                    if (!galItem) return;
                    var img = galItem.querySelector('.card-image');
                    if (img) {
                        img.src = data.image_base64;
                    } else {
                        // Was a placeholder — replace with an image container
                        var placeholder = galItem.querySelector('.card-image-placeholder');
                        if (placeholder) {
                            var con = document.createElement('div');
                            con.className = 'card-image-container';
                            var newImg = document.createElement('img');
                            newImg.src = data.image_base64;
                            newImg.alt = cardName;
                            newImg.className = 'card-image';
                            con.appendChild(newImg);
                            placeholder.replaceWith(con);
                        }
                    }
                })
                .catch(function () {});
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

    // ── Bootstrap ─────────────────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', function () {
        var tabsEl = document.querySelector('.deck-tabs');
        if (!tabsEl) return;   // Not a deck page — skip

        // Deck name from URL: /deck/<name>
        var parts = window.location.pathname.split('/');
        _deckName    = parts[2] ? decodeURIComponent(parts[2]) : '';
        _stagedCount = parseInt(tabsEl.dataset.stagedCount || '0', 10);

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
         'ef-artist', 'ef-frame', 'ef-dfc-type'].forEach(function (id) {
            var el = $id(id);
            if (!el) return;
            el.addEventListener('input', onFormChange);
            el.addEventListener('change', onFormChange);
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

        // Forge buttons
        var forgeBtn = $id('forge-btn');
        if (forgeBtn) forgeBtn.addEventListener('click', function () { onForgeClick(false); });
        var closeForgeBtnEl = $id('close-forge-btn');
        if (closeForgeBtnEl) closeForgeBtnEl.addEventListener('click', function () { onForgeClick(true); });

        // Create Card button
        var createCardBtn = $id('create-card-btn');
        if (createCardBtn) createCardBtn.addEventListener('click', openNewCardEditor);

        // Assembly Line buttons
        var forgeAllBtn = $id('forge-all-btn');
        if (forgeAllBtn) forgeAllBtn.addEventListener('click', onForgeAllClick);

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
    });

}());
