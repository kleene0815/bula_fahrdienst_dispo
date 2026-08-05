// Sitzbedarf einer Fahrt: Belegung pro Fahrtabschnitt statt Summe aller Personen.
//
// Die Route ist immer Lager → Stopp 1 → … → Stopp N → Lager (Segmente 0..N).
// Hinfahrten steigen am Lager ein und am eigenen Stopp aus (Segmente 0..j),
// Abholungen steigen am eigenen Stopp ein und fahren bis zum Lager (Segmente j+1..N).
// Benötigte Sitze = 1 (Fahrer) + maximale gleichzeitige Belegung über alle Segmente.
//
// `orders` muss die Aufträge in Stopp-Reihenfolge enthalten.
export function computeNeededSeats(orders) {
  const n = orders.length
  const segments = new Array(n + 1).fill(0)
  orders.forEach((o, j) => {
    if (o.trip_type === 'besorgung' || !o.patient_name) return
    const persons = 1 + (o.companion ? 1 : 0)
    // Unbekannter Fahrttyp mit Patient: konservativ auf allen Segmenten einrechnen
    const start = o.trip_type === 'abholung' ? j + 1 : 0
    const end = o.trip_type === 'hinfahrt' ? j : n
    for (let k = start; k <= end; k++) segments[k] += persons
  })
  return 1 + Math.max(0, ...segments)
}
