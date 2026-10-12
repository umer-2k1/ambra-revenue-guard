// Plain-English meanings for the codes/jargon shown across the app.
// Used in hover tooltips so non-experts get it and experts keep the codes.

export const CARC = {
  'CO-16': 'The payer says the claim is missing information it needs to make a decision.',
  'CO-50': 'The payer decided the service was not medically necessary.',
  'CO-197': 'No prior authorization was on file for this transport.',
  'CO-4': 'The procedure code and the modifier do not match.',
  'CO-151': 'The payer thinks the documentation does not support this level or frequency of service.',
  'CO-29': 'The claim was filed after the payer’s filing deadline.',
  'CO-18': 'This looks like a duplicate of a claim that was already processed.',
  'CO-22': 'Another insurer may be responsible (coordination of benefits).',
}

export const CPT = {
  A0425: 'Basic life support (BLS) non-emergency ambulance transport.',
  A0427: 'Advanced life support (ALS) level 1 — emergency transport.',
  A0428: 'Basic life support (BLS) emergency transport.',
  A0429: 'Advanced life support (ALS) level 1 — non-emergency transport.',
  A0433: 'Advanced life support (ALS) level 2 — higher-acuity care.',
  A0434: 'Specialty care transport (e.g. critical care between facilities).',
}

export const SERVICE = {
  'ALS-1 Emergency': 'Advanced life support, emergency — paramedic-level emergency transport.',
  'ALS-1 Non-Emergency': 'Advanced life support, non-emergency.',
  'ALS-2': 'Advanced life support level 2 — the most advanced ground transport.',
  'BLS Emergency': 'Basic life support, emergency — EMT-level emergency transport.',
  'BLS Non-Emergency': 'Basic life support, non-emergency (e.g. scheduled stretcher trips).',
  SCT: 'Specialty care transport — moving a critical patient between facilities.',
}

export const TERM = {
  ALS: 'Advanced Life Support — paramedic-level care.',
  BLS: 'Basic Life Support — EMT-level care.',
  PCR: 'Patient Care Report — the run sheet a crew writes at the scene.',
  POV: 'Privately Owned Vehicle — a personal car, not an ambulance.',
  PCS: 'Physician Certification Statement — a doctor’s signed note that the transport was medically necessary.',
  CARC: 'Claim Adjustment Reason Code — the payer’s standard reason for a denial.',
  RARC: 'Remittance Advice Remark Code — extra detail attached to a denial.',
  CPT: 'Current Procedural Terminology — the billing code for the service performed.',
  DOS: 'Date of service.',
}

export const carcMeaning = (c) => CARC[c]
export const cptMeaning = (c) => CPT[c]
export const serviceMeaning = (s) => SERVICE[s]
export const termMeaning = (t) => TERM[t]
