// Moteur de suggestions : sans interface, sans réseau, entièrement testable.
//
// Principe : des exclusions strictes (sexe, longueur, initiales, composés, prénoms écartés), puis un score
// pour ordonner ce qui reste (préférences du questionnaire + goûts appris des prénoms gardés / écartés).
// Si les exclusions laissent trop peu de prénoms, on les assouplit une à une et on le dit.

// --- Données -----------------------------------------------------------------------------------------

/** Transforme profils.v1.json (colonnes + lignes) en objets, avec les champs dérivés utiles aux suggestions. */
export function decoderProfils(json) {
  const col = Object.fromEntries(json.colonnes.map((nom, i) => [nom, i]))
  return json.lignes.map((l) => {
    const p = {
      id: l[col.id],
      affichage: l[col.affichage],
      sexe: l[col.sexe],
      recF: l[col.rec_f],
      recM: l[col.rec_m],
      rangF: l[col.rang_f],
      rangM: l[col.rang_m],
      pic: l[col.pic],
      debut: l[col.debut],
      lettres: l[col.lettres],
      syllabes: l[col.syllabes],
      accent: l[col.accent] === 1,
      compose: l[col.compose] === 1,
      tend: l[col.tend],
      origines: l[col.orig] ? l[col.orig].split('|') : [],
      qualite: l[col.qualite],
    }
    p.rec = p.recF + p.recM
    p.initiale = initialeDe(p.id)
    p.finale = finaleDe(p.id, 1)
    p.finale2 = finaleDe(p.id, 2)
    return p
  })
}

const sansAccent = (t) => t.normalize('NFD').replace(/\p{M}/gu, '')
const lettresDe = (id) => sansAccent(id.toLowerCase()).replace(/[^a-z]/g, '')
export const initialeDe = (id) => lettresDe(id).charAt(0)
const finaleDe = (id, n) => lettresDe(id).slice(-n)

// --- Classes (popularité, style, longueur) ---------------------------------------------------------

/** Seuils en naissances par an (moyenne des dernières années) : voir STATISTIQUES.md. */
export const SEUILS_POPULARITE = { courant: 500, connu: 80 }

export const POPULARITES = ['courant', 'connu', 'rare']
export const STYLES = ['intemporel', 'vintage', 'moderne']
export const LONGUEURS = ['court', 'moyen', 'long']

/** Naissances annuelles récentes dans le sexe visé (tous sexes si aucun n'est précisé). */
export function recentes(p, sexe) {
  if (sexe === 'F') return p.recF
  if (sexe === 'M') return p.recM
  return p.rec
}

export function classePopularite(p, sexe = 'tous') {
  const n = recentes(p, sexe)
  return n >= SEUILS_POPULARITE.courant ? 'courant' : n >= SEUILS_POPULARITE.connu ? 'connu' : 'rare'
}

export function classeLongueur(p) {
  return p.lettres <= 4 ? 'court' : p.lettres <= 6 ? 'moyen' : 'long'
}

/**
 * Styles d'un prénom (un prénom peut en avoir plusieurs) :
 * - intemporel : donné depuis longtemps (≥ 50 naissances/an avant 1925) et encore bien présent ;
 * - vintage    : sommet avant 1960 et plus guère donné, ou « retour » ;
 * - moderne    : décollage récent (≥ 50 naissances/an seulement depuis 1985) ou tendance émergente.
 */
export function stylesDe(p) {
  const s = []
  if (p.debut != null && p.debut < 1925 && p.rec >= 100 && !p.tend.includes('d')) s.push('intemporel')
  if ((p.pic < 1960 && p.rec < 100) || p.tend.includes('r')) s.push('vintage')
  if ((p.debut != null && p.debut >= 1985) || p.tend.includes('e') || (p.tend.includes('p') && p.pic >= 2000)) s.push('moderne')
  return s
}

/** Un prénom est-il envisageable pour ce sexe ? (mixte = prénom d'usage mixte). */
export function convientAuSexe(p, sexe) {
  if (sexe === 'tous') return true
  if (sexe === 'X') return p.sexe === 'X'
  return p.sexe === sexe || p.sexe === 'X'
}

// --- Préférences -------------------------------------------------------------------------------------

export const PREFERENCES_VIDES = {
  sexe: 'tous', // tous | F | M | X
  popularite: 'tous', // tous | courant | connu | rare
  style: 'tous', // tous | intemporel | vintage | moderne
  longueur: 'tous', // tous | court | moyen | long
  compose: 'tous', // tous | non (sans prénoms composés)
  initialesEvitees: [], // lettres a–z
  initialesVoulues: [],
  origines: [], // familles d'origine souhaitées
  aimes: [], // identifiants de prénoms déjà aimés (points de départ)
  exclus: [], // identifiants de prénoms à ne jamais proposer
}

export function preferencesVides() {
  return structuredClone(PREFERENCES_VIDES)
}

export function aDesPreferences(prefs) {
  const v = PREFERENCES_VIDES
  return ['sexe', 'popularite', 'style', 'longueur', 'compose'].some((k) => prefs[k] !== v[k]) ||
    ['initialesEvitees', 'initialesVoulues', 'origines', 'aimes', 'exclus'].some((k) => prefs[k].length)
}

// --- Exclusions strictes, avec assouplissement progressif ------------------------------------------

/** Ce qu'on assouplit, dans l'ordre, quand il reste trop peu de prénoms. Le sexe et les exclus ne sont jamais assouplis. */
export const ASSOUPLISSEMENTS = ['initialesVoulues', 'longueur', 'initialesEvitees', 'compose']

export function convient(p, prefs, ignores = []) {
  if (!convientAuSexe(p, prefs.sexe)) return false
  if (prefs.exclus.includes(p.id)) return false
  if (!ignores.includes('longueur') && prefs.longueur !== 'tous' && classeLongueur(p) !== prefs.longueur) return false
  if (!ignores.includes('compose') && prefs.compose === 'non' && p.compose) return false
  if (!ignores.includes('initialesEvitees') && prefs.initialesEvitees.includes(p.initiale)) return false
  if (!ignores.includes('initialesVoulues') && prefs.initialesVoulues.length && !prefs.initialesVoulues.includes(p.initiale)) return false
  return true
}

/**
 * Prénoms retenus par les exclusions. `ecartes` : identifiants déjà vus (gardés ou écartés).
 * Renvoie { liste, assouplis } ; `assouplis` nomme les exclusions levées (jamais le sexe ni les exclus).
 */
export function candidats(profils, prefs, vus = new Set(), minimum = 30) {
  const ignores = []
  const libres = (ig) => profils.filter((p) => !vus.has(p.id) && convient(p, prefs, ig))
  let liste = libres(ignores)
  for (const regle of ASSOUPLISSEMENTS) {
    if (liste.length >= minimum) break
    ignores.push(regle)
    liste = libres(ignores)
  }
  return { liste, assouplis: ignores.filter((r) => estDemandee(prefs, r)) }
}

// Une règle n'est signalée comme assouplie que si le visiteur l'avait réellement demandée.
function estDemandee(prefs, regle) {
  if (regle === 'longueur') return prefs.longueur !== 'tous'
  if (regle === 'compose') return prefs.compose !== 'tous'
  return prefs[regle].length > 0
}

// --- Goûts appris ----------------------------------------------------------------------------------

/** Traits d'un prénom utilisés pour apprendre ce que le visiteur aime. */
export function traits(p) {
  return [
    `lettres:${p.lettres <= 3 ? 3 : p.lettres >= 9 ? 9 : p.lettres}`,
    `syl:${Math.min(p.syllabes, 4)}`,
    `init:${p.initiale}`,
    `fin:${p.finale}`,
    `fin2:${p.finale2}`,
    `pop:${classePopularite(p)}`,
    `epoque:${p.pic}`,
    ...p.origines.map((o) => `orig:${o}`),
    ...(p.accent ? ['accent'] : []),
    ...(p.compose ? ['compose'] : []),
  ]
}

/**
 * Poids de chaque trait d'après les choix : +1 par prénom gardé, −1 par prénom écarté, lissé
 * (un trait vu une seule fois pèse peu). Les prénoms « aimés » au départ comptent comme gardés.
 */
export function apprendre(parId, gardes, ecartes, aimes = []) {
  const somme = new Map()
  const compte = new Map()
  const ajouter = (id, signe) => {
    const p = parId.get(id)
    if (!p) return
    for (const t of traits(p)) {
      somme.set(t, (somme.get(t) || 0) + signe)
      compte.set(t, (compte.get(t) || 0) + 1)
    }
  }
  for (const id of [...gardes, ...aimes]) ajouter(id, 1)
  for (const id of ecartes) ajouter(id, -1)
  const poids = new Map()
  for (const [t, s] of somme) poids.set(t, s / (compte.get(t) + 2))
  return poids
}

// --- Score -----------------------------------------------------------------------------------------

const RANG_POPULARITE = { courant: 0, connu: 1, rare: 2 }

/**
 * Score d'un prénom et raisons lisibles. Les préférences du questionnaire pèsent plus que les goûts
 * appris tant que peu de choix ont été faits ; un prénom d'origine inconnue n'est jamais pénalisé.
 */
export function scorer(p, prefs, appris = new Map(), nbChoix = 0) {
  let score = 0
  const raisons = []

  if (prefs.popularite !== 'tous') {
    const ecart = Math.abs(RANG_POPULARITE[classePopularite(p, prefs.sexe)] - RANG_POPULARITE[prefs.popularite])
    score += ecart === 0 ? 2 : ecart === 1 ? 0.3 : -1.5
    if (ecart === 0) raisons.push(LIBELLES_RAISON.popularite[prefs.popularite])
  }
  if (prefs.style !== 'tous') {
    if (stylesDe(p).includes(prefs.style)) {
      score += 2
      raisons.push(LIBELLES_RAISON.style[prefs.style])
    } else score -= 0.8
  }
  if (prefs.origines.length && p.origines.length) {
    const communes = p.origines.filter((o) => prefs.origines.includes(o))
    if (communes.length) {
      score += 2.5
      raisons.push(`Origine ${communes[0]}`)
    } else score -= 0.5
  }
  if (prefs.longueur !== 'tous') raisons.push(LIBELLES_RAISON.longueur[prefs.longueur])
  if (prefs.initialesVoulues.length) raisons.push(`Commence par ${p.initiale.toUpperCase()}`)

  if (appris.size) {
    const ts = traits(p)
    const affinite = ts.reduce((s, t) => s + (appris.get(t) || 0), 0) / Math.sqrt(ts.length)
    // Les goûts appris prennent de l'importance au fil des choix (plafonnés).
    score += affinite * Math.min(3, 0.6 + nbChoix * 0.15)
    if (affinite > 1.2) raisons.push('Proche de ceux que vous gardez')
  }
  return { score, raisons }
}

const LIBELLES_RAISON = {
  popularite: { courant: 'Très courant', connu: 'Connu sans être partout', rare: 'Rare et original' },
  style: { intemporel: 'Intemporel', vintage: 'Vintage', moderne: 'Moderne' },
  longueur: { court: 'Court', moyen: 'Longueur moyenne', long: 'Long' },
}

// --- Tirage -----------------------------------------------------------------------------------------

/** Générateur pseudo-aléatoire reproductible (tests) : mulberry32. */
export function hasard(graine = Date.now()) {
  let a = graine >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * Prochaines suggestions. Pas de répétition (`vus`), diversité (initiale et finale différentes de celles
 * qui viennent d'être proposées) et, tant que les goûts sont inconnus, bonus d'exploration pour varier
 * popularité, longueur et époque.
 *
 * etat = { gardes, ecartes, vus (ids déjà montrés ou en attente) }
 * Renvoie { suggestions: [{ prenom, score, raisons }], assouplis }.
 */
export function suggerer(profils, prefs, etat, n = 10, rng = Math.random) {
  const parId = new Map(profils.map((p) => [p.id, p]))
  const vus = new Set([...etat.gardes, ...etat.ecartes, ...(etat.vus || [])])
  const { liste, assouplis } = candidats(profils, prefs, vus)
  const nbChoix = etat.gardes.length + etat.ecartes.length
  const appris = apprendre(parId, etat.gardes, etat.ecartes, prefs.aimes)
  const exploration = nbChoix < 10 && !aDesPreferences({ ...prefs, sexe: 'tous', exclus: [] })

  const base = liste.map((p) => {
    const { score, raisons } = scorer(p, prefs, appris, nbChoix)
    let s = score + rng() * 1.2
    // Sans préférence de popularité, on favorise légèrement les prénoms que l'on croise réellement.
    if (prefs.popularite === 'tous') s += Math.min(1, Math.log10(recentes(p, prefs.sexe) + 1) / 3) * 0.8
    return { prenom: p, score: s, raisons }
  })
  base.sort((a, b) => b.score - a.score)

  // Classes de popularité et de longueur déjà rencontrées dans les choix (pour l'exploration).
  const vuesPop = new Set()
  const vuesLong = new Set()
  for (const id of [...etat.gardes, ...etat.ecartes]) {
    const p = parId.get(id)
    if (p) {
      vuesPop.add(classePopularite(p, prefs.sexe))
      vuesLong.add(classeLongueur(p))
    }
  }
  const recents = (etat.recents || []).map((id) => parId.get(id)).filter(Boolean)
  const choisis = []
  const reserve = base.slice(0, Math.max(n * 8, 60))
  while (choisis.length < n && reserve.length) {
    const derniers = [...recents, ...choisis.map((c) => c.prenom)].slice(-3)
    let meilleur = 0
    let meilleurScore = -Infinity
    reserve.forEach(({ prenom: p, score }, i) => {
      let s = score
      for (const r of derniers) {
        if (r.initiale === p.initiale) s -= 0.9
        if (r.finale2 === p.finale2) s -= 0.9
      }
      if (exploration) {
        // Varier popularité et longueur pour que les premiers choix révèlent les goûts.
        const pop = classePopularite(p, prefs.sexe)
        s -= choisis.filter((c) => classePopularite(c.prenom, prefs.sexe) === pop).length * 0.5
        if (!vuesPop.has(pop)) s += 0.4
        if (!vuesLong.has(classeLongueur(p))) s += 0.3
      }
      if (s > meilleurScore) {
        meilleurScore = s
        meilleur = i
      }
    })
    choisis.push(reserve.splice(meilleur, 1)[0])
  }
  return { suggestions: choisis, assouplis }
}
