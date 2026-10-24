// Rangs des classements publiés.

/**
 * Classement officiel : les fichiers sont triés par rang officiel Insee, contigu de 1 à n
 * (vérifié par les tests du pipeline), donc rang = position + 1.
 */
export function avecRangOfficiel(liste) {
  return liste.map(([id, valeur], i) => ({ id, valeur, rang: i + 1 }))
}

/**
 * Classement calculé (somme d'effectifs arrondis) : les ex æquo partagent le même rang
 * (rang = 1 + nombre de prénoms ayant un total strictement supérieur).
 */
export function avecRangCalcule(liste) {
  let rang = 0
  return liste.map(([id, valeur], i) => {
    if (i === 0 || valeur < liste[i - 1][1]) rang = i + 1
    return { id, valeur, rang }
  })
}
