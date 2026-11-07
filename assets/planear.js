/* Planee su consulta (portada): cotizador, guía de servicio y lista de preparación.
   Los precios y el calendario vienen de <script id="planear-datos">, que build.py llena con las
   tablas de plantilla.html: aquí no hay ningún precio escrito a mano. No se envía ni se guarda nada
   fuera del navegador; la lista se recuerda solo en este dispositivo (localStorage). */
(function () {
  'use strict';
  var raiz = document.getElementById('planear-app');
  var datosEl = document.getElementById('planear-datos');
  if (!raiz || !datosEl) return;
  var D = JSON.parse(datosEl.textContent);
  var lang = (document.documentElement.lang || 'es').slice(0, 2);
  var quieto = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var T = {
    es: {
      tabs: ['Cotizador', '¿Qué servicio me conviene?', 'Prepare su consulta'],
      svc: { consultorio: 'Consultorio', hotel: 'Visita a hotel', domicilio: 'Consulta a domicilio', teleconsulta: 'Teleconsulta' },
      svcDesc: { consultorio: 'Del Valle, Roma o Polanco', hotel: 'En su habitación, 24 h según disponibilidad', domicilio: 'En su casa, en la Ciudad de México', teleconsulta: 'Por videollamada' },
      paso: ['¿Qué servicio necesita?', '¿Dónde?', '¿Cuándo?', 'Extras'],
      sede: 'Sede', zona: 'Zona', otraZona: 'Otra zona', tipo: 'Tipo de consulta', primera: 'Primera vez', subsecuente: 'Subsecuente',
      seguimiento: 'Es una consulta de seguimiento', fecha: 'Fecha', hora: 'Hora',
      iv: 'Hidratación intravenosa, si el médico la indica', ivNota: 'Solo adultos (18 años o más). El médico valora primero; si no está indicada, no se cobran los {iv}; la enfermería tampoco, salvo que haya pedido que la enfermera llegue junto con el médico.',
      junto: 'Prefiero que la enfermera llegue junto con el médico', juntoNota: 'Así evita esperar alrededor de 1 h 30 min, pero el honorario de enfermería se cobra aunque la hidratación no esté indicada.',
      asistente: 'Asistente de traducción al francés', sinAsistente: 'La asistente de francés no está disponible en esa fecha: la consulta será en español o inglés y no se cobra la asistente.', asistenteNota: 'Apoyo administrativo y de traducción; no realiza actos médicos. Mismo honorario que enfermería; no se incluye en el pago en línea: se paga directamente en la consulta. Avise por WhatsApp con anticipación para confirmar su disponibilidad.',
      elija: 'Elija un servicio para ver el costo.', faltaFecha: 'Elija fecha y hora para calcular.',
      cerrado: 'El consultorio no abre ese día. Horario: lunes a viernes de 17:00 a 20:00 y sábado de 11:00 a 15:00.',
      sinServicio: 'Sin servicio en esa fecha y hora. Elija otra fecha.', soloTele: 'Ese día no hay consulta presencial (consultorio, hotel ni domicilio). La teleconsulta sí está disponible y se agenda por WhatsApp.', fueraAnio: 'Para fechas posteriores, consulte por WhatsApp.',
      solo20: 'La cita de las 20:00 es solo para consultas subsecuentes.',
      zonaOtra: 'Esa zona se cotiza por WhatsApp.',
      horario: ['Horario ordinario', 'Horario especial', 'Festivo oficial'],
      motivo: { oficial: 'festivo oficial', tradicional: 'festivo tradicional', domingo: 'domingo', sabado: 'sábado después de las 15:00', noche: 'noche (20:01 a 08:59)' },
      linea: { consulta: 'Consulta', subsecuente: 'Consulta subsecuente', festivo: 'Consulta en día festivo', visita: 'Visita', seguimiento: 'Seguimiento a domicilio', iv: 'Hidratación intravenosa (si está indicada)', enf: 'Honorario de enfermería', asis: 'Asistente de traducción al francés', tele: 'Teleconsulta' },
      total: 'Total estimado', sinIV: 'Si la hidratación no está indicada',
      cuando: { consultorio: ['Al reservar en línea (100 % de la consulta)', 'En el consultorio, el día de la cita'], domicilio: ['Anticipo por transferencia (50 % de la tarifa ordinaria)', 'Al médico, en la visita'], hotel: [null, 'Al médico, en la visita (sin anticipo)'], teleconsulta: ['Antes de la videollamada', null] },
      pago: {
        consultorio: 'Al reservar en línea se paga el 100 % de la consulta ({a}). Ese pago no es reembolsable, pero puede reprogramar sin costo si avisa con 24 horas o más. Si le conviene más, agende por WhatsApp: se confirma con una transferencia del 50 % ({b}), el resto se paga en el consultorio y, si cancela con 24 horas o más, se le devuelve (si fue transferencia bancaria directa). La asistente de traducción, si la eligió, se paga en el consultorio. Después de reservar, envíe un WhatsApp.',
        consultorioFestivo: 'Los días festivos se coordinan por WhatsApp; no se reservan en línea.',
        hotel: 'Sin anticipo: se paga directamente al médico, en pesos (tarjeta, transferencia o efectivo).',
        domicilio: 'Se solicita por WhatsApp y se confirma con una transferencia del 50 % de la tarifa ordinaria de su zona ({a}); el resto, incluidas la hidratación intravenosa y la enfermería si se aplican, se paga al médico en la visita.',
        cancelaWA: 'Si cancela con 24 horas o más de anticipación, se le devuelve la transferencia, siempre que haya sido bancaria directa, sin aplicaciones ni plataformas de pago.',
        teleconsulta: 'Se agenda por WhatsApp; el pago completo se hace antes de la videollamada y ahí se le indica cómo pagar.', teleFestivo: 'Se agenda por WhatsApp; el pago completo se hace antes de la videollamada.'
      },
      aviso: 'Estimación con los honorarios publicados. El médico confirma el total al coordinar su cita. No incluye procedimientos, medicamentos ni documentos. No se atienden menores de 15 años ni personas embarazadas.',
      wa: 'Enviar por WhatsApp', reservar: 'Reservar consultorio', reiniciar: 'Empezar de nuevo',
      waHola: 'Hola, Dr. Ortega-Arenas, quiero solicitar', waTotal: 'Total estimado en la web', waCierre: '¿Tiene disponibilidad?',
      g: {
        alarmaT: '¿Tiene alguno de estos signos ahora?', alarmaS: 'Marque los que apliquen. Esta lista no es completa: si cree que es una emergencia, llame al 911.',
        alarma: ['Dolor u opresión en el pecho, o dolor en brazo, mandíbula, cuello o espalda, con falta de aire, debilidad o sensación de desmayo", "Dificultad para respirar que aparece de pronto o empeora, o falta de aire en reposo", "Signos de EVC de aparición súbita: cara caída, brazo débil, habla arrastrada, pérdida de equilibrio o de la visión", "Pérdida del estado de alerta, desmayo, confusión súbita o dificultad para despertar a la persona", "Convulsión", "Sangrado abundante que no se detiene con presión directa, o vómito o evacuaciones con mucha sangre", "Reacción alérgica grave: hinchazón de labios, lengua o garganta, dificultad para respirar o tragar, o ronchas extensas con mareo", "Dolor abdominal intenso o que no cede, sobre todo con el abdomen duro", "Fiebre con rigidez de nuca, dolor de cabeza intenso, confusión o sensibilidad a la luz", "Deshidratación grave: no poder beber ni retener líquidos, orinar muy poco o nada, somnolencia o confusión", "Golpe en la cabeza con vómito, somnolencia o confusión; accidente de tránsito; posible fractura o herida profunda'],
        ninguno: 'Ninguno de estos', continuar: 'Continuar',
        urgT: 'Llame al 911 o acuda a urgencias ahora', urgS: 'Estos signos necesitan atención de urgencias. Este servicio es ambulatorio y no atiende urgencias. Si está en un hotel, avise también a la recepción.', urgLink: 'Ver la guía: cuándo ir a urgencias →',
        quienT: '¿Quién es el paciente?', quien: ['Tiene 15 años o más y no está embarazada', 'Es menor de 15 años', 'Está embarazada'],
        noT: 'Este servicio no atiende a menores de 15 años ni a personas embarazadas', noS: 'Acuda con un pediatra o con su ginecólogo-obstetra. Ante una emergencia, llame al 911.',
        dondeT: '¿Dónde está?', donde: ['En un hotel de la Ciudad de México', 'En una casa de la Ciudad de México', 'Puedo ir a un consultorio', 'Fuera de la Ciudad de México'],
        explT: '¿Necesita que lo revisen en persona?', expl: ['Sí: tengo síntomas que hay que revisar', 'No: renovar o revisar una receta (el médico decide si procede), revisar estudios, un seguimiento o una duda'],
        resT: 'Servicio sugerido', calcular: 'Calcular el costo', atras: 'Atrás',
        res: {
          hotel: 'El médico va a su habitación, según disponibilidad. Escriba por WhatsApp para coordinar la hora de llegada.',
          domicilio: 'El médico va a su casa. Se solicita por WhatsApp.',
          consultorio: 'Consulta en Del Valle, Roma o Polanco, con cita en línea o por WhatsApp.',
          teleconsulta: 'Por videollamada, sin traslados; se agenda por WhatsApp. Si en la llamada se necesita una exploración física, el médico se lo indicará.',
          lejos: 'Si no puede trasladarse a la Ciudad de México, la opción es la teleconsulta. Si necesita una exploración física, acuda con un médico local.'
        },
        frances: 'Si quiere la consulta enteramente en francés, avise por WhatsApp para confirmar a la asistente de traducción.'
      },
      l: {
        titulo: 'Su lista', servicio: 'Su servicio', frances: 'Quiero la consulta en francés', listo: '¡Todo listo para su consulta!', borrar: 'Borrar marcas', enviar: 'Enviar por WhatsApp', copiar: 'Copiar lista', copiado: 'Lista copiada.', compartirT: 'Lista para mi consulta con el Dr. Ortega-Arenas ({s}):', compartirF: 'Formularios: drcjortegaarenas.com/formularios', local: 'Sus marcas se guardan solo en este dispositivo.',
        comun: [['form1', 'Llenar el consentimiento informado', '/formularios/'], ['form2', 'Llenar el cuestionario de salud', '/formularios/'], ['id', 'Tener a la mano su identificación oficial (INE o pasaporte): el consentimiento pide una foto'], ['meds', 'Anotar sus medicamentos con dosis, y sus alergias'], ['estudios', 'Reunir sus estudios previos (puede adjuntarlos en el cuestionario)']],
        consultorio: [['res', 'Reservar en línea y pagar la consulta (o agendar por WhatsApp con anticipo del 50 %)'], ['wa', 'Enviar un WhatsApp después de reservar']],
        hotel: [['wa', 'Escribir por WhatsApp para coordinar la visita'], ['recep', 'Avisar a la recepción que espera al médico y dar su número de habitación'], ['pago', 'Tener lista la forma de pago en pesos: tarjeta, transferencia o efectivo']],
        domicilio: [['wa', 'Solicitar la visita por WhatsApp'], ['ant', 'Hacer la transferencia del anticipo (50 % de la tarifa ordinaria de su zona)'], ['dir', 'Tener lista su dirección completa y una referencia']],
        teleconsulta: [['wa', 'Agendar la teleconsulta por WhatsApp'], ['pago', 'Hacer el pago antes de la videollamada (por WhatsApp se le indica cómo)'], ['app', 'Tener lista la app de la videollamada (Google Meet, WhatsApp o FaceTime) y buena conexión']],
        fr: ['fr', 'Avisar por WhatsApp con anticipación para confirmar a la asistente de traducción'], frNo: 'La asistente de traducción no está disponible en teleconsulta ni a domicilio.'
      }
    },
    en: {
      tabs: ['Cost estimator', 'Which service is right for me?', 'Prepare your visit'],
      svc: { consultorio: 'Clinic visit', hotel: 'Hotel visit', domicilio: 'House call', teleconsulta: 'Telemedicine' },
      svcDesc: { consultorio: 'Del Valle, Roma or Polanco', hotel: 'In your room, 24 h subject to availability', domicilio: 'At your home in Mexico City', teleconsulta: 'By video call' },
      paso: ['Which service do you need?', 'Where?', 'When?', 'Extras'],
      sede: 'Location', zona: 'Area', otraZona: 'Other area', tipo: 'Type of visit', primera: 'First visit', subsecuente: 'Follow-up',
      seguimiento: 'This is a follow-up visit', fecha: 'Date', hora: 'Time',
      iv: 'IV hydration, if the physician prescribes it', ivNota: 'Adults only (18 and older). The physician assesses first; if it is not indicated, the {iv} fee is not charged, and neither is the nursing fee unless you asked for the nurse to arrive with the physician.',
      junto: 'I prefer the nurse to arrive together with the physician', juntoNota: 'This avoids waiting about 1 h 30 min, but the nursing fee is charged even if IV hydration is not indicated.',
      asistente: 'French translation assistant', sinAsistente: 'The French assistant is not available on that date: the visit will be in Spanish or English and there is no assistant fee.', asistenteNota: 'Administrative and translation support only; she does not provide any medical care. Same fee as the nurse; it is not included in the online payment and is paid directly at the visit. Let us know in advance on WhatsApp so we can confirm her availability.',
      elija: 'Choose a service to see the cost.', faltaFecha: 'Choose a date and time to calculate.',
      cerrado: 'The clinic is closed that day. Hours: Monday to Friday 5–8 pm and Saturday 11 am–3 pm.',
      sinServicio: 'No service on that date and time. Please choose another date.', soloTele: 'There are no in-person visits that day (clinic, hotel or house call). Telemedicine is available and is booked on WhatsApp.', fueraAnio: 'For later dates, please ask on WhatsApp.',
      solo20: 'The 8:00 pm slot is for follow-up visits only.',
      zonaOtra: 'That area is quoted on WhatsApp.',
      horario: ['Standard hours', 'Special hours', 'Official public holiday'],
      motivo: { oficial: 'official public holiday', tradicional: 'traditional holiday', domingo: 'Sunday', sabado: 'Saturday after 3:00 pm', noche: 'night (8:01 pm–8:59 am)' },
      linea: { consulta: 'Visit', subsecuente: 'Follow-up visit', festivo: 'Holiday visit', visita: 'Visit', seguimiento: 'Follow-up house call', iv: 'IV hydration (if indicated)', enf: 'Nursing fee', asis: 'French translation assistant', tele: 'Telemedicine' },
      total: 'Estimated total', sinIV: 'If IV hydration is not indicated',
      cuando: { consultorio: ['When booking online (100% of the consultation)', 'At the clinic, on the day of the visit'], domicilio: ['Deposit by bank transfer (50% of the standard fee)', 'To the physician, at the visit'], hotel: [null, 'To the physician, at the visit (no deposit)'], teleconsulta: ['Before the video call', null] },
      pago: {
        consultorio: 'When booking online you pay 100% of the consultation ({a}). This payment is non-refundable, but you can reschedule free of charge with at least 24 hours’ notice. If it suits you better, book on WhatsApp: it is confirmed with a 50% bank transfer ({b}), the rest is paid at the clinic and, if you cancel at least 24 hours ahead, it is refunded (if it was a direct bank transfer). The translation assistant, if you chose her, is paid at the clinic. After booking, please send a WhatsApp message.',
        consultorioFestivo: 'Holidays are arranged on WhatsApp; they cannot be booked online.',
        hotel: 'No deposit: you pay the physician directly, in Mexican pesos (card, transfer or cash).',
        domicilio: 'Requested on WhatsApp and confirmed with a bank transfer of 50% of the standard fee for your area ({a}); the rest, including IV hydration and nursing if given, is paid to the physician at the visit.',
        cancelaWA: 'If you cancel at least 24 hours in advance, your transfer is refunded, as long as it was a direct bank transfer, not made through an app or payment platform.',
        teleconsulta: 'Booked on WhatsApp; full payment is made before the video call, and we tell you how to pay there.', teleFestivo: 'Booked on WhatsApp; full payment is made before the video call.'
      },
      aviso: 'Estimate based on the published fees. The physician confirms the total when arranging your visit. Procedures, medications and documents are not included. We do not see patients under 15 years of age or pregnant patients.',
      wa: 'Send on WhatsApp', reservar: 'Book a clinic visit', reiniciar: 'Start over',
      waHola: 'Hello Dr. Ortega-Arenas, I would like to request', waTotal: 'Estimated total on the website', waCierre: 'Are you available?',
      g: {
        alarmaT: 'Do you have any of these signs right now?', alarmaS: 'Check any that apply. This list is not complete: if you think it is an emergency, call 911.',
        alarma: ['Chest pain or pressure, or pain in the arm, jaw, neck or back, with shortness of breath, weakness or feeling faint", "Trouble breathing that starts suddenly or gets worse, or shortness of breath at rest", "Sudden signs of a stroke: facial droop, arm weakness, slurred speech, loss of balance or vision", "Loss of consciousness, fainting, sudden confusion or difficulty waking the person", "A seizure", "Heavy bleeding that does not stop with direct pressure, or vomit or stools with a lot of blood", "A severe allergic reaction: swelling of the lips, tongue or throat, trouble breathing or swallowing, or widespread hives with dizziness", "Severe abdominal pain or pain that does not ease, especially with a hard belly", "Fever with a stiff neck, severe headache, confusion or sensitivity to light", "Severe dehydration: unable to drink or keep fluids down, passing little or no urine, drowsiness or confusion", "A blow to the head followed by vomiting, drowsiness or confusion; a traffic accident; a possible broken bone or a deep wound'],
        ninguno: 'None of these', continuar: 'Continue',
        urgT: 'Call 911 or go to an emergency room now', urgS: 'These signs need emergency care. This is an outpatient service and does not handle emergencies. If you are at a hotel, also tell the front desk.', urgLink: 'Read the guide: when to go to the ER →',
        quienT: 'Who is the patient?', quien: ['Aged 15 or older and not pregnant', 'Under 15 years old', 'Pregnant'],
        noT: 'This service does not see patients under 15 years of age or pregnant patients', noS: 'Please see a pediatrician or your obstetrician. In an emergency, call 911.',
        dondeT: 'Where are you?', donde: ['At a hotel in Mexico City', 'At a home in Mexico City', 'I can go to a clinic', 'Outside Mexico City'],
        explT: 'Do you need an in-person examination?', expl: ['Yes: I have symptoms that need to be checked', 'No: renewing or reviewing a prescription (the physician decides if appropriate), reviewing test results, a follow-up or a question'],
        resT: 'Suggested service', calcular: 'Estimate the cost', atras: 'Back',
        res: {
          hotel: 'The physician comes to your room, subject to availability. Send a WhatsApp message to arrange the arrival time.',
          domicilio: 'The physician comes to your home. Requested on WhatsApp.',
          consultorio: 'A clinic visit in Del Valle, Roma or Polanco, booked online or on WhatsApp.',
          teleconsulta: 'By video call, no travel needed; booked on WhatsApp. If a physical examination is needed during the call, the physician will tell you.',
          lejos: 'If you cannot travel to Mexico City, the option is telemedicine. If you need a physical examination, please see a local doctor.'
        },
        frances: 'If you want the visit entirely in French, let us know on WhatsApp so we can confirm the translation assistant.'
      },
      l: {
        titulo: 'Your checklist', servicio: 'Your service', frances: 'I want the visit in French', listo: 'You are all set for your visit!', borrar: 'Clear checkmarks', enviar: 'Send on WhatsApp', copiar: 'Copy list', copiado: 'List copied.', compartirT: 'Checklist for my visit with Dr. Ortega-Arenas ({s}):', compartirF: 'Forms: drcjortegaarenas.com/formularios', local: 'Your checkmarks are saved only on this device.',
        comun: [['form1', 'Fill in the informed consent form', '/formularios/'], ['form2', 'Fill in the health questionnaire', '/formularios/'], ['id', 'Have your official ID (passport or INE) at hand: the consent form asks for a photo'], ['meds', 'Write down your medications with doses, and your allergies'], ['estudios', 'Gather your previous test results (you can attach them to the questionnaire)']],
        consultorio: [['res', 'Book online and pay the consultation (or book on WhatsApp with a 50% deposit)'], ['wa', 'Send a WhatsApp message after booking']],
        hotel: [['wa', 'Send a WhatsApp message to arrange the visit'], ['recep', 'Tell the front desk you are expecting the physician and give your room number'], ['pago', 'Have your payment ready in Mexican pesos: card, transfer or cash']],
        domicilio: [['wa', 'Request the visit on WhatsApp'], ['ant', 'Make the deposit transfer (50% of the standard fee for your area)'], ['dir', 'Have your full address and a landmark ready']],
        teleconsulta: [['wa', 'Book the video call on WhatsApp'], ['pago', 'Pay before the video call (we tell you how on WhatsApp)'], ['app', 'Have the video call app ready (Google Meet, WhatsApp or FaceTime) and a good connection']],
        fr: ['fr', 'Let us know on WhatsApp in advance so we can confirm the translation assistant'], frNo: 'The translation assistant is not available for telemedicine or house calls.'
      }
    },
    fr: {
      tabs: ['Estimation du coût', 'Quel service me convient ?', 'Préparez votre consultation'],
      svc: { consultorio: 'Cabinet', hotel: 'Visite à l’hôtel', domicilio: 'Visite à domicile', teleconsulta: 'Téléconsultation' },
      svcDesc: { consultorio: 'Del Valle, Roma ou Polanco', hotel: 'Dans votre chambre, 24 h/24 selon disponibilité', domicilio: 'Chez vous, à Mexico', teleconsulta: 'Par appel vidéo' },
      paso: ['De quel service avez-vous besoin ?', 'Où ?', 'Quand ?', 'Options'],
      sede: 'Cabinet', zona: 'Quartier', otraZona: 'Autre quartier', tipo: 'Type de consultation', primera: 'Première consultation', subsecuente: 'Suivi',
      seguimiento: 'Il s’agit d’une visite de suivi', fecha: 'Date', hora: 'Heure',
      iv: 'Hydratation intraveineuse, si le médecin la prescrit', ivNota: 'Adultes uniquement (18 ans ou plus). Le médecin évalue d’abord ; si elle n’est pas indiquée, les {iv} ne sont pas facturés, ni les honoraires infirmiers, sauf si vous avez demandé que l’infirmière arrive avec le médecin.',
      junto: 'Je préfère que l’infirmière arrive avec le médecin', juntoNota: 'Vous évitez ainsi d’attendre environ 1 h 30, mais ses honoraires sont facturés même si l’hydratation n’est pas indiquée.',
      asistente: 'Assistante de traduction en français', sinAsistente: 'L’assistante francophone n’est pas disponible à cette date : la consultation se déroulera en espagnol ou en anglais et l’assistante n’est pas facturée.', asistenteNota: 'Soutien administratif et de traduction uniquement ; elle ne réalise aucun acte médical. Mêmes honoraires que l’infirmière ; ils ne sont pas inclus dans le paiement en ligne et se règlent directement lors de la consultation. Prévenez-nous à l’avance par WhatsApp pour vérifier sa disponibilité.',
      elija: 'Choisissez un service pour voir le coût.', faltaFecha: 'Choisissez une date et une heure pour calculer.',
      cerrado: 'Le cabinet est fermé ce jour-là. Horaires : du lundi au vendredi de 17 h à 20 h et le samedi de 11 h à 15 h.',
      sinServicio: 'Aucun service à cette date et à cette heure. Choisissez une autre date.', soloTele: 'Pas de consultation en présentiel ce jour-là (cabinet, hôtel ou domicile). La téléconsultation reste possible et se réserve par WhatsApp.', fueraAnio: 'Pour des dates ultérieures, renseignez-vous par WhatsApp.',
      solo20: 'Le créneau de 20 h est réservé aux consultations de suivi.',
      zonaOtra: 'Ce quartier fait l’objet d’un devis par WhatsApp.',
      horario: ['Horaires ordinaires', 'Horaires spéciaux', 'Jour férié officiel'],
      motivo: { oficial: 'jour férié officiel', tradicional: 'jour férié traditionnel', domingo: 'dimanche', sabado: 'samedi après 15 h', noche: 'nuit (20 h 01 – 8 h 59)' },
      linea: { consulta: 'Consultation', subsecuente: 'Consultation de suivi', festivo: 'Consultation un jour férié', visita: 'Visite', seguimiento: 'Visite de suivi à domicile', iv: 'Hydratation intraveineuse (si indiquée)', enf: 'Honoraires infirmiers', asis: 'Assistante de traduction en français', tele: 'Téléconsultation' },
      total: 'Total estimé', sinIV: 'Si l’hydratation n’est pas indiquée',
      cuando: { consultorio: ['En réservant en ligne (100 % de la consultation)', 'Au cabinet, le jour du rendez-vous'], domicilio: ['Acompte par virement (50 % du tarif ordinaire)', 'Au médecin, lors de la visite'], hotel: [null, 'Au médecin, lors de la visite (sans acompte)'], teleconsulta: ['Avant l’appel vidéo', null] },
      pago: {
        consultorio: 'En réservant en ligne, vous payez 100 % de la consultation ({a}). Ce paiement n’est pas remboursable, mais vous pouvez reporter le rendez-vous sans frais en prévenant au moins 24 heures à l’avance. Si cela vous convient mieux, réservez par WhatsApp : le rendez-vous est confirmé par un virement de 50 % ({b}), le reste se règle au cabinet et, si vous annulez au moins 24 heures à l’avance, il vous est remboursé (s’il s’agit d’un virement bancaire direct). L’assistante de traduction, si vous l’avez choisie, se règle au cabinet. Après la réservation, envoyez un message WhatsApp.',
        consultorioFestivo: 'Les jours fériés se planifient par WhatsApp ; ils ne se réservent pas en ligne.',
        hotel: 'Sans acompte : vous payez directement le médecin, en pesos (carte, virement ou espèces).',
        domicilio: 'Se demande par WhatsApp et se confirme par un virement de 50 % du tarif ordinaire de votre quartier ({a}) ; le reste, y compris l’hydratation intraveineuse et les soins infirmiers le cas échéant, se règle au médecin lors de la visite.',
        cancelaWA: 'Si vous annulez au moins 24 heures à l’avance, votre virement vous est remboursé, à condition qu’il s’agisse d’un virement bancaire direct, sans application ni plateforme de paiement.',
        teleconsulta: 'Se réserve par WhatsApp ; le paiement complet se fait avant l’appel vidéo et nous vous indiquons comment payer.', teleFestivo: 'Se réserve par WhatsApp ; le paiement complet se fait avant l’appel vidéo.'
      },
      aviso: 'Estimation selon les honoraires publiés. Le médecin confirme le total en planifiant votre rendez-vous. Les actes, les médicaments et les documents ne sont pas inclus. Nous ne recevons pas les patients de moins de 15 ans ni les personnes enceintes.',
      wa: 'Envoyer par WhatsApp', reservar: 'Réserver au cabinet', reiniciar: 'Recommencer',
      waHola: 'Bonjour Dr Ortega-Arenas, je souhaite demander', waTotal: 'Total estimé sur le site', waCierre: 'Avez-vous des disponibilités ?',
      g: {
        alarmaT: 'Avez-vous l’un de ces signes en ce moment ?', alarmaS: 'Cochez ce qui s’applique. Cette liste n’est pas exhaustive : si vous pensez qu’il s’agit d’une urgence, appelez le 911.',
        alarma: ['Douleur ou oppression dans la poitrine, ou douleur dans le bras, la mâchoire, le cou ou le dos, avec essoufflement, faiblesse ou sensation d’évanouissement", "Difficulté à respirer qui apparaît brusquement ou s’aggrave, ou essoufflement au repos", "Signes soudains d’AVC : visage qui tombe, bras faible, parole pâteuse, perte d’équilibre ou de vision", "Perte de connaissance, évanouissement, confusion soudaine ou difficulté à réveiller la personne", "Crise convulsive", "Saignement abondant qui ne s’arrête pas par une pression directe, ou vomissements ou selles contenant beaucoup de sang", "Réaction allergique grave : gonflement des lèvres, de la langue ou de la gorge, difficulté à respirer ou à avaler, ou urticaire étendue avec étourdissements", "Douleur abdominale intense ou qui ne cède pas, surtout si le ventre est dur", "Fièvre avec raideur de la nuque, mal de tête intense, confusion ou sensibilité à la lumière", "Déshydratation grave : impossibilité de boire ou de garder les liquides, très peu ou pas d’urine, somnolence ou confusion", "Coup à la tête suivi de vomissements, de somnolence ou de confusion ; accident de la route ; fracture possible ou plaie profonde'],
        ninguno: 'Aucun de ces signes', continuar: 'Continuer',
        urgT: 'Appelez le 911 ou allez aux urgences maintenant', urgS: 'Ces signes nécessitent des soins d’urgence. Ce service est ambulatoire et ne prend pas en charge les urgences. Si vous êtes à l’hôtel, prévenez aussi la réception.', urgLink: 'Lire le guide : quand aller aux urgences →',
        quienT: 'Qui est le patient ?', quien: ['15 ans ou plus et pas enceinte', 'Moins de 15 ans', 'Enceinte'],
        noT: 'Ce service ne reçoit pas les patients de moins de 15 ans ni les personnes enceintes', noS: 'Consultez un pédiatre ou votre gynécologue-obstétricien. En cas d’urgence, appelez le 911.',
        dondeT: 'Où êtes-vous ?', donde: ['Dans un hôtel à Mexico', 'Dans un logement à Mexico', 'Je peux aller au cabinet', 'En dehors de Mexico'],
        explT: 'Avez-vous besoin d’un examen en personne ?', expl: ['Oui : j’ai des symptômes à examiner', 'Non : renouveler ou revoir une ordonnance (le médecin décide si c’est approprié), des résultats à revoir, un suivi ou une question'],
        resT: 'Service suggéré', calcular: 'Estimer le coût', atras: 'Retour',
        res: {
          hotel: 'Le médecin vient dans votre chambre, selon disponibilité. Écrivez par WhatsApp pour convenir de l’heure d’arrivée.',
          domicilio: 'Le médecin vient chez vous. Se demande par WhatsApp.',
          consultorio: 'Consultation à Del Valle, Roma ou Polanco, sur rendez-vous en ligne ou par WhatsApp.',
          teleconsulta: 'Par appel vidéo, sans déplacement ; se réserve par WhatsApp. Si un examen physique est nécessaire pendant l’appel, le médecin vous le dira.',
          lejos: 'Si vous ne pouvez pas vous rendre à Mexico, l’option est la téléconsultation. Si vous avez besoin d’un examen physique, consultez un médecin sur place.'
        },
        frances: 'Pour une consultation entièrement en français, prévenez-nous par WhatsApp pour confirmer l’assistante de traduction.'
      },
      l: {
        titulo: 'Votre liste', servicio: 'Votre service', frances: 'Je souhaite la consultation en français', listo: 'Tout est prêt pour votre consultation !', borrar: 'Effacer les coches', enviar: 'Envoyer par WhatsApp', copiar: 'Copier la liste', copiado: 'Liste copiée.', compartirT: 'Liste pour ma consultation avec le Dr Ortega-Arenas ({s}) :', compartirF: 'Formulaires : drcjortegaarenas.com/formularios', local: 'Vos coches sont enregistrées uniquement sur cet appareil.',
        comun: [['form1', 'Remplir le consentement éclairé', '/formularios/'], ['form2', 'Remplir le questionnaire de santé', '/formularios/'], ['id', 'Avoir votre pièce d’identité (passeport ou carte d’identité) : le consentement demande une photo'], ['meds', 'Noter vos médicaments avec les doses, et vos allergies'], ['estudios', 'Rassembler vos examens antérieurs (vous pouvez les joindre au questionnaire)']],
        consultorio: [['res', 'Réserver en ligne et payer la consultation (ou réserver par WhatsApp avec un acompte de 50 %)'], ['wa', 'Envoyer un message WhatsApp après la réservation']],
        hotel: [['wa', 'Écrire par WhatsApp pour organiser la visite'], ['recep', 'Prévenir la réception que vous attendez le médecin et donner votre numéro de chambre'], ['pago', 'Prévoir le paiement en pesos : carte, virement ou espèces']],
        domicilio: [['wa', 'Demander la visite par WhatsApp'], ['ant', 'Faire le virement de l’acompte (50 % du tarif ordinaire de votre quartier)'], ['dir', 'Préparer votre adresse complète et un point de repère']],
        teleconsulta: [['wa', 'Réserver la téléconsultation par WhatsApp'], ['pago', 'Payer avant l’appel vidéo (nous vous indiquons comment par WhatsApp)'], ['app', 'Préparer l’application d’appel vidéo (Google Meet, WhatsApp ou FaceTime) et une bonne connexion']],
        fr: ['fr', 'Prévenir à l’avance par WhatsApp pour confirmer l’assistante de traduction'], frNo: 'L’assistante de traduction n’est pas disponible en téléconsultation ni à domicile.'
      }
    }
  };
  var L = T[lang] || T.es;
  var URGENCIAS = { es: '/guias/cuando-ir-a-urgencias/', en: '/en/guides/emergency-care-mexico-city/', fr: '/fr/guides/urgences-mexico/' }[lang] || '/guias/cuando-ir-a-urgencias/';

  /* ── utilidades ───────────────────────────── */
  function h(tag, attrs, hijos) {
    var el = document.createElement(tag);
    for (var k in attrs || {}) {
      if (k === 'text') el.textContent = attrs[k];
      else if (k === 'html') el.innerHTML = attrs[k];
      else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== false && attrs[k] != null) el.setAttribute(k, attrs[k] === true ? '' : attrs[k]);
    }
    (hijos || []).forEach(function (c) { if (c) el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return el;
  }
  function mxn(n) { return '$' + Math.round(n).toLocaleString('en-US') + ' MXN'; }
  function minutos(hora) { var p = hora.split(':'); return +p[0] * 60 + +p[1]; }
  function hoy() { var d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  var ULTIMA = D.oficiales.concat(D.tradicionales).sort().pop().slice(0, 4) + '-12-31';
  function diaSemana(f) { var p = f.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]).getDay(); }
  function fechaBonita(f) { var p = f.split('-'); return p[2] + '/' + p[1] + '/' + p[0]; }

  // Regla de la web: festivo = oficial (24 h); especial = noches 20:01–08:59, sábado desde 15:01, domingo y festivos tradicionales.
  function horario(f, hora) {
    if (D.oficiales.indexOf(f) >= 0) return { n: 2, por: 'oficial' };
    if (D.tradicionales.indexOf(f) >= 0) return { n: 1, por: 'tradicional' };
    var dia = diaSemana(f), m = minutos(hora);
    if (dia === 0) return { n: 1, por: 'domingo' };
    if (dia === 6) return (m >= 540 && m <= 900) ? { n: 0 } : { n: 1, por: m > 900 ? 'sabado' : 'noche' };
    return (m >= 540 && m <= 1200) ? { n: 0 } : { n: 1, por: 'noche' };
  }
  function sinServicio(f, hora, svc) {
    return D.sinServicio.some(function (s) { return s.fecha === f && minutos(hora) >= minutos(s.desde) && !(s.teleconsulta && svc === 'teleconsulta'); });
  }
  function horasConsultorio(f) {
    var dia = diaSemana(f);
    if (dia >= 1 && dia <= 5) return ['17:00', '18:00', '19:00', '20:00'];
    if (dia === 6) return ['11:00', '12:00', '13:00', '14:00'];
    return [];
  }
  function horasTele(f) {
    var dia = diaSemana(f), out = [], i;
    if (D.oficiales.indexOf(f) >= 0 || dia === 0 || dia === 6) { for (i = 11; i <= 14; i++) out.push(String(i).padStart(2, '0') + ':00'); }
    else { for (i = 10; i <= 18; i++) out.push(String(i).padStart(2, '0') + ':00'); }
    return out;
  }

  /* ── cálculo (puro, para poder probarlo) ──── */
  function asistente(s, hz, add, r) {
    if ((D.sinAsistente || []).indexOf(s.fecha) >= 0) { r.notas.push(L.sinAsistente); return; }
    add(L.linea.asis, D.asistente[hz.n]);
    r.notas.push(L.asistenteNota);
  }

  function cotizar(s) {
    var r = { lineas: [], total: 0, notas: [], error: null, horario: null, reservar: null };
    if (!s.svc) { r.error = L.elija; return r; }
    if (s.svc !== 'teleconsulta' && s.svc !== 'consultorio' && s.zona === 'otra') { r.error = L.zonaOtra; return r; }
    var lista = s.svc === 'hotel' ? D.hotel.zonas : s.svc === 'domicilio' ? D.domicilio : null;  // zona retirada o desconocida
    if ((lista && !lista[s.zona]) || (s.svc === 'consultorio' && !D.consultorio[s.sede])) { r.error = L.zonaOtra; return r; }
    if (!s.fecha || !s.hora) { r.error = L.faltaFecha; return r; }
    if (s.fecha > ULTIMA) { r.error = L.fueraAnio; return r; }
    if (sinServicio(s.fecha, s.hora, s.svc)) { r.error = s.svc !== 'teleconsulta' && D.sinServicio.some(function (x) { return x.fecha === s.fecha && x.teleconsulta; }) ? L.soloTele : L.sinServicio; return r; }
    var hz = horario(s.fecha, s.hora);
    r.horario = hz;
    var add = function (txt, monto) { r.lineas.push([txt, monto]); r.total += monto; };
    if (s.svc === 'consultorio') {
      var sede = D.consultorio[s.sede];
      if (horasConsultorio(s.fecha).length === 0) { r.error = L.cerrado; return r; }
      if (s.hora === '20:00' && s.tipo !== 'subsecuente') { r.error = L.solo20; return r; }
      if (hz.n === 2) { add(L.linea.festivo, D.consultorioFestivo); r.notas.push(L.pago.consultorioFestivo); }
      else {
        var sub = s.tipo === 'subsecuente' && sede.subsecuente;
        add(sub ? L.linea.subsecuente : L.linea.consulta, sub ? sede.subsecuente : sede.precio);
        if (hz.por === 'tradicional') r.notas.push(L.pago.consultorioFestivo);  // ese día no se reserva en línea
        else {
          r.ahora = r.total;  // en Cal.com se paga el 100 % de la consulta
          r.notas.push(L.pago.consultorio.replace('{a}', mxn(r.ahora)).replace('{b}', mxn(r.total / 2)));
          r.reservar = D.cal[s.sede];
        }
      }
      if (s.asistente) asistente(s, hz, add, r);
    } else if (s.svc === 'hotel') {
      var letra = D.hotel.zonas[s.zona];
      add(L.linea.visita + ' · ' + s.zona, D.hotel[letra][hz.n]);
      r.notas.push(L.pago.hotel);
    } else if (s.svc === 'domicilio') {
      var area = D.domicilio[s.zona];
      if (s.seguimiento && area.seguimiento && hz.n === 0) add(L.linea.seguimiento + ' · ' + s.zona, area.seguimiento);
      else add(L.linea.visita + ' · ' + s.zona, area.precios[hz.n]);
      r.ahora = area.precios[0] / 2;
      r.notas.push(L.pago.domicilio.replace('{a}', mxn(r.ahora)), L.pago.cancelaWA);
    } else if (s.svc === 'teleconsulta') {
      if (hz.n === 2) { add(L.linea.tele, D.teleconsulta[1]); r.notas.push(L.pago.teleFestivo); }
      else { add(L.linea.tele, D.teleconsulta[0]); r.notas.push(L.pago.teleconsulta); }
      r.notas.push(L.pago.cancelaWA);
    }
    if ((s.svc === 'hotel' || s.svc === 'domicilio') && s.iv) {
      r.base = r.total + (s.junto ? D.enfermeria[hz.n] : 0);
      add(L.linea.iv, D.iv);
      add(L.linea.enf, D.enfermeria[hz.n]);
      r.notas.push(L.ivNota.replace('{iv}', mxn(D.iv)));
      if (s.junto) r.notas.push(L.juntoNota);
    }
    if (s.svc === 'hotel' && s.asistente) asistente(s, hz, add, r);
    if (s.svc === 'hotel') r.ahora = 0;
    if (s.svc === 'teleconsulta') r.ahora = r.total;
    if (r.ahora != null) r.despues = r.total - r.ahora;
    return r;
  }

  /* ── animaciones ──────────────────────────── */
  function contar(el, hasta) {
    var desde = +(el.dataset.valor || 0);
    el.dataset.valor = hasta;
    if (quieto || desde === hasta) { el.textContent = mxn(hasta); return; }
    var t0 = null, dur = 650;
    function paso(t) {
      if (!t0) t0 = t;
      var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = mxn(desde + (hasta - desde) * e);
      if (p < 1) requestAnimationFrame(paso);
    }
    requestAnimationFrame(paso);
  }
  function entrar(el) {
    if (quieto) return;
    el.classList.remove('pl-entra'); void el.offsetWidth; el.classList.add('pl-entra');
  }

  /* ── pestañas ─────────────────────────────── */
  raiz.innerHTML = '';
  var lista = h('div', { class: 'pl-tabs', role: 'tablist', 'aria-label': L.tabs.join(' · ') });
  var paneles = [];
  var indicador = h('span', { class: 'pl-tab-ind', 'aria-hidden': 'true' });
  L.tabs.forEach(function (nombre, i) {
    var b = h('button', { type: 'button', class: 'pl-tab', role: 'tab', id: 'pl-tab-' + i, 'aria-controls': 'pl-panel-' + i, 'aria-selected': i === 0 ? 'true' : 'false', tabindex: i === 0 ? '0' : '-1', text: nombre });
    b.addEventListener('click', function () { abrir(i); });
    b.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); var j = (i + (e.key === 'ArrowRight' ? 1 : 2)) % 3; abrir(j); lista.children[j].focus(); }
    });
    lista.appendChild(b);
    paneles.push(h('div', { class: 'pl-panel', role: 'tabpanel', id: 'pl-panel-' + i, 'aria-labelledby': 'pl-tab-' + i, hidden: i !== 0 }));
  });
  lista.appendChild(indicador);
  raiz.appendChild(lista);
  paneles.forEach(function (p) { raiz.appendChild(p); });
  function moverIndicador() {
    var b = lista.querySelector('[aria-selected="true"]');
    indicador.style.width = b.offsetWidth + 'px';
    indicador.style.transform = 'translateX(' + b.offsetLeft + 'px)';
  }
  function abrir(i) {
    Array.prototype.forEach.call(lista.querySelectorAll('.pl-tab'), function (b, j) { b.setAttribute('aria-selected', j === i ? 'true' : 'false'); b.tabIndex = j === i ? 0 : -1; });
    paneles.forEach(function (p, j) { p.hidden = j !== i; });
    moverIndicador(); entrar(paneles[i]);
  }
  window.addEventListener('resize', moverIndicador);

  /* ── cotizador ────────────────────────────── */
  var S = { svc: null, sede: 'Del Valle', tipo: 'primera', zona: null, fecha: '', hora: '', iv: false, junto: false, asistente: false, seguimiento: false };
  var URLP = new URLSearchParams(location.search), PREF = URLP.get('zona');
  function zonaPara(svc) {
    var lista = svc === 'hotel' ? D.hotel.zonas : svc === 'domicilio' ? D.domicilio : null;
    if (!lista) return null;
    return PREF && lista[PREF] ? PREF : (svc === 'hotel' ? 'Roma' : 'Del Valle');
  }
  if (PREF && D.consultorio[PREF]) S.sede = PREF;
  if (['consultorio', 'hotel', 'domicilio', 'teleconsulta'].indexOf(URLP.get('cotizar')) >= 0) {
    S.svc = URLP.get('cotizar'); S.zona = zonaPara(S.svc);
    S.iv = URLP.get('iv') === '1' && (S.svc === 'hotel' || S.svc === 'domicilio');
  }
  var P0 = paneles[0];
  var formulario = h('div', { class: 'pl-form' });
  var resultado = h('div', { class: 'pl-result', 'aria-live': 'polite' });
  P0.appendChild(h('div', { class: 'pl-cot' }, [formulario, resultado]));

  function chips(nombre, opciones, valor, alElegir, conDesc) {
    var g = h('div', { class: 'pl-chips' + (conDesc ? ' pl-chips-desc' : ''), role: 'radiogroup', 'aria-label': nombre });
    opciones.forEach(function (o) {
      var b = h('button', { type: 'button', class: 'pl-chip', role: 'radio', 'aria-checked': o.v === valor ? 'true' : 'false' }, [h('span', { class: 'pl-chip-t', text: o.t }), o.d ? h('span', { class: 'pl-chip-d', text: o.d }) : null]);
      b.addEventListener('click', function () { alElegir(o.v); });
      g.appendChild(b);
    });
    return g;
  }
  function campo(titulo, control, nota) {
    return h('div', { class: 'pl-field' }, [h('p', { class: 'pl-label', text: titulo }), control, nota ? h('p', { class: 'pl-note', text: nota }) : null]);
  }
  function casilla(texto, valor, alCambiar, nota) {
    var id = 'pl-c-' + Math.random().toString(36).slice(2, 8);
    var input = h('input', { type: 'checkbox', id: id, checked: valor });
    input.addEventListener('change', function () { alCambiar(input.checked); });
    return h('div', { class: 'pl-check' }, [input, h('label', { for: id }, [h('span', { text: texto }), nota ? h('small', { text: nota }) : null])]);
  }
  function paso(n, titulo, contenido) {
    return h('fieldset', { class: 'pl-step' }, [h('legend', {}, [h('span', { class: 'pl-step-n', text: String(n) }), titulo])].concat(contenido));
  }

  function dibujarForm() {
    formulario.innerHTML = '';
    formulario.appendChild(paso(1, L.paso[0], [chips(L.paso[0], ['consultorio', 'hotel', 'domicilio', 'teleconsulta'].map(function (k) { return { v: k, t: L.svc[k], d: L.svcDesc[k] }; }), S.svc, function (v) {
      var nuevo = S.svc !== v;
      S.svc = v;
      if (nuevo) { S.hora = ''; S.zona = zonaPara(v); S.iv = S.junto = S.asistente = S.seguimiento = false; }
      dibujarForm(); calcular(); entrar(formulario.lastElementChild);
    }, true)]));
    if (!S.svc) return;
    var n = 2;
    if (S.svc === 'consultorio') {
      formulario.appendChild(paso(n++, L.paso[1], [
        campo(L.sede, chips(L.sede, Object.keys(D.consultorio).map(function (k) { return { v: k, t: k }; }), S.sede, function (v) { S.sede = v; dibujarForm(); calcular(); })),
        campo(L.tipo, chips(L.tipo, [{ v: 'primera', t: L.primera }, { v: 'subsecuente', t: L.subsecuente }], S.tipo, function (v) { S.tipo = v; dibujarForm(); calcular(); }))
      ]));
    } else if (S.svc === 'hotel' || S.svc === 'domicilio') {
      var zonas = Object.keys(S.svc === 'hotel' ? D.hotel.zonas : D.domicilio);
      var sel = h('select', { class: 'pl-select', 'aria-label': L.zona });
      zonas.concat(['otra']).forEach(function (z) { sel.appendChild(h('option', { value: z, selected: z === S.zona, text: z === 'otra' ? L.otraZona : z })); });
      sel.addEventListener('change', function () { S.zona = sel.value; S.seguimiento = false; dibujarForm(); calcular(); });
      var cont = [campo(L.zona, sel)];
      if (S.svc === 'domicilio' && D.domicilio[S.zona] && D.domicilio[S.zona].seguimiento) cont.push(casilla(L.seguimiento, S.seguimiento, function (v) { S.seguimiento = v; calcular(); }));
      formulario.appendChild(paso(n++, L.paso[1], cont));
    }
    var fecha = h('input', { type: 'date', class: 'pl-input', min: hoy(), max: ULTIMA, value: S.fecha, 'aria-label': L.fecha });
    fecha.addEventListener('change', function () { S.fecha = fecha.value; if (S.svc === 'consultorio' || S.svc === 'teleconsulta') S.hora = ''; dibujarForm(); calcular(); });
    var hora;
    if (S.svc === 'consultorio' || S.svc === 'teleconsulta') {
      var horas = S.fecha ? (S.svc === 'consultorio' ? horasConsultorio(S.fecha) : horasTele(S.fecha)) : [];
      hora = h('select', { class: 'pl-select', 'aria-label': L.hora, disabled: !horas.length });
      hora.appendChild(h('option', { value: '', text: '—' }));
      horas.forEach(function (x) { hora.appendChild(h('option', { value: x, selected: x === S.hora, text: x })); });
    } else {
      hora = h('input', { type: 'time', class: 'pl-input', step: 900, value: S.hora, 'aria-label': L.hora });
    }
    hora.addEventListener('change', function () { S.hora = hora.value; calcular(); });
    formulario.appendChild(paso(n++, L.paso[2], [h('div', { class: 'pl-row' }, [campo(L.fecha, fecha), campo(L.hora, hora)])]));
    var extras = [];
    if (S.svc === 'hotel' || S.svc === 'domicilio') {
      extras.push(casilla(L.iv, S.iv, function (v) { S.iv = v; if (!v) S.junto = false; dibujarForm(); calcular(); }));
      if (S.iv) extras.push(casilla(L.junto, S.junto, function (v) { S.junto = v; calcular(); }, L.juntoNota));
    }
    if (S.svc === 'consultorio' || S.svc === 'hotel') extras.push(casilla(L.asistente, S.asistente, function (v) { S.asistente = v; calcular(); }));
    if (extras.length) formulario.appendChild(paso(n++, L.paso[3], extras));
  }

  var totalEl = h('p', { class: 'pl-total-n', text: mxn(0) });
  function calcular() {
    var r = cotizar(S);
    resultado.innerHTML = '';
    if (r.error) {
      resultado.appendChild(h('p', { class: 'pl-empty', text: r.error }));
      if (r.error === L.zonaOtra || r.error === L.fueraAnio) resultado.appendChild(botonWA(mensaje(null)));
      totalEl.dataset.valor = 0;
      return;
    }
    var etiqueta = L.horario[r.horario.n] + (r.horario.por ? ' · ' + L.motivo[r.horario.por] : '');
    resultado.appendChild(h('span', { class: 'pl-badge pl-badge-' + r.horario.n, text: etiqueta }));
    var tabla = h('dl', { class: 'pl-lines' });
    r.lineas.forEach(function (l) { tabla.appendChild(h('div', {}, [h('dt', { text: l[0] }), h('dd', { text: mxn(l[1]) })])); });
    resultado.appendChild(tabla);
    resultado.appendChild(h('div', { class: 'pl-total' }, [h('p', { class: 'pl-total-l', text: L.total }), totalEl]));
    contar(totalEl, r.total);
    if (r.base != null) resultado.appendChild(h('p', { class: 'pl-sub', text: L.sinIV + ': ' + mxn(r.base) }));
    var cuando = L.cuando[S.svc];
    if (r.ahora != null && cuando) {
      var pagos = h('dl', { class: 'pl-lines pl-pagos' });
      if (cuando[0] && r.ahora) pagos.appendChild(h('div', {}, [h('dt', { text: cuando[0] }), h('dd', { text: mxn(r.ahora) })]));
      if (cuando[1] && r.despues) pagos.appendChild(h('div', {}, [h('dt', { text: cuando[1] }), h('dd', { text: mxn(r.despues) })]));
      if (pagos.children.length) resultado.appendChild(pagos);
    }
    var notas = h('ul', { class: 'pl-notes' });
    r.notas.concat([L.aviso]).forEach(function (t) { notas.appendChild(h('li', { text: t })); });
    resultado.appendChild(notas);
    var acciones = h('div', { class: 'pl-actions' }, [botonWA(mensaje(r))]);
    if (r.reservar) acciones.appendChild(h('a', { class: 'hero-cta ghost', href: r.reservar, target: '_blank', rel: 'noopener', text: L.reservar }));
    resultado.appendChild(acciones);
  }
  function mensaje(r) {
    var partes = [L.waHola + ': ' + (S.svc ? L.svc[S.svc] : '')];
    if (S.svc === 'consultorio') partes.push(S.sede + ' (' + (S.tipo === 'subsecuente' ? L.subsecuente : L.primera) + ')');
    else if (S.zona && S.zona !== 'otra') partes.push(S.zona);
    if (S.fecha && S.hora) partes.push(fechaBonita(S.fecha) + ' ' + S.hora + (r && r.horario ? ' (' + L.horario[r.horario.n] + ')' : ''));
    if (S.svc === 'domicilio' && S.seguimiento) partes.push(L.seguimiento);
    if (S.iv) partes.push(L.linea.iv);
    if (S.asistente) partes.push(L.linea.asis);
    if (r && r.total) partes.push(L.waTotal + ': ' + mxn(r.total));
    var cuando = r && L.cuando[S.svc];
    if (cuando && r.ahora != null) {
      if (cuando[0] && r.ahora) partes.push(cuando[0] + ': ' + mxn(r.ahora));
      if (cuando[1] && r.despues) partes.push(cuando[1] + ': ' + mxn(r.despues));
    }
    return partes.join(' · ') + '. ' + L.waCierre;
  }
  function botonWA(texto) {
    return h('a', { class: 'hero-cta', href: 'https://wa.me/' + D.whatsapp + '?text=' + encodeURIComponent(texto), target: '_blank', rel: 'noopener', text: L.wa });
  }
  dibujarForm(); calcular();

  /* ── guía de servicio ─────────────────────── */
  var P1 = paneles[1], G = L.g, pasos = 4;
  var guia = h('div', { class: 'pl-guide' });
  var barra = h('div', { class: 'pl-progress', 'aria-hidden': 'true' }, [h('span')]);
  P1.appendChild(barra); P1.appendChild(guia);
  var respuestas = {};
  function avance(n) { barra.firstChild.style.width = Math.round(n / pasos * 100) + '%'; }
  function opcionesGuia(titulo, opciones, alElegir, atras) {
    guia.innerHTML = '';
    guia.appendChild(h('h3', { class: 'pl-q', text: titulo }));
    var g = h('div', { class: 'pl-options' });
    opciones.forEach(function (o, i) { g.appendChild(h('button', { type: 'button', class: 'pl-option', text: o, onclick: function () { alElegir(i); } })); });
    guia.appendChild(g);
    if (atras) guia.appendChild(h('button', { type: 'button', class: 'pl-back', text: '← ' + G.atras, onclick: atras }));
    entrar(guia);
  }
  function guiaAlarma() {
    avance(0); respuestas = {};
    guia.innerHTML = '';
    guia.appendChild(h('h3', { class: 'pl-q', text: G.alarmaT }));
    guia.appendChild(h('p', { class: 'pl-note', text: G.alarmaS }));
    var marcadas = [];
    var caja = h('div', { class: 'pl-alarms' });
    G.alarma.forEach(function (t, i) { caja.appendChild(casilla(t, false, function (v) { marcadas[i] = v; seguir.textContent = marcadas.some(Boolean) ? G.continuar : G.ninguno; })); });
    guia.appendChild(caja);
    var seguir = h('button', { type: 'button', class: 'hero-cta', text: G.ninguno, onclick: function () { marcadas.some(Boolean) ? guiaUrgencia() : guiaQuien(); } });
    guia.appendChild(h('div', { class: 'pl-actions' }, [seguir]));
    entrar(guia);
  }
  function guiaUrgencia() {
    avance(4);
    guia.innerHTML = '';
    guia.appendChild(h('div', { class: 'pl-alert' }, [
      h('p', { class: 'pl-alert-t', text: G.urgT }), h('p', { text: G.urgS }),
      h('div', { class: 'pl-actions' }, [h('a', { class: 'hero-cta pl-911', href: 'tel:911', text: '911' }), h('a', { class: 'hero-cta ghost', href: URGENCIAS, text: G.urgLink })])
    ]));
    guia.appendChild(h('button', { type: 'button', class: 'pl-back', text: '← ' + L.reiniciar, onclick: guiaAlarma }));
    entrar(guia);
  }
  function guiaQuien() {
    avance(1);
    opcionesGuia(G.quienT, G.quien, function (i) {
      if (i > 0) {
        avance(4);
        guia.innerHTML = '';
        guia.appendChild(h('div', { class: 'pl-alert pl-alert-soft' }, [h('p', { class: 'pl-alert-t', text: G.noT }), h('p', { text: G.noS })]));
        guia.appendChild(h('button', { type: 'button', class: 'pl-back', text: '← ' + L.reiniciar, onclick: guiaAlarma }));
        entrar(guia);
      } else guiaDonde();
    }, guiaAlarma);
  }
  function guiaDonde() {
    avance(2);
    opcionesGuia(G.dondeT, G.donde, function (i) { respuestas.donde = i; i === 3 ? guiaResultado('teleconsulta', G.res.lejos) : guiaExpl(); }, guiaQuien);
  }
  function guiaExpl() {
    avance(3);
    opcionesGuia(G.explT, G.expl, function (i) {
      if (i === 1) return guiaResultado('teleconsulta', G.res.teleconsulta);
      var svc = ['hotel', 'domicilio', 'consultorio'][respuestas.donde];
      guiaResultado(svc, G.res[svc]);
    }, guiaDonde);
  }
  function guiaResultado(svc, texto) {
    avance(4);
    guia.innerHTML = '';
    var tarjeta = h('div', { class: 'pl-reco' }, [h('p', { class: 'pl-label', text: G.resT }), h('h3', { class: 'pl-reco-t', text: L.svc[svc] }), h('p', { text: texto })]);
    if (lang === 'fr' && svc !== 'teleconsulta' && svc !== 'domicilio') tarjeta.appendChild(h('p', { class: 'pl-note', text: G.frances }));
    var acciones = h('div', { class: 'pl-actions' }, [
      h('button', { type: 'button', class: 'hero-cta', text: G.calcular, onclick: function () { S.svc = svc; S.zona = zonaPara(svc); S.hora = ''; dibujarForm(); calcular(); lServicio = svc; dibujarLista(); abrir(0); } }),
      h('a', { class: 'hero-cta ghost', href: 'https://wa.me/' + D.whatsapp + '?text=' + encodeURIComponent(L.waHola + ': ' + L.svc[svc] + '. ' + L.waCierre), target: '_blank', rel: 'noopener', text: L.wa })
    ]);
    tarjeta.appendChild(acciones);
    guia.appendChild(tarjeta);
    guia.appendChild(h('button', { type: 'button', class: 'pl-back', text: '← ' + L.reiniciar, onclick: guiaAlarma }));
    entrar(guia);
  }
  guiaAlarma();

  /* ── lista de preparación ─────────────────── */
  var P2 = paneles[2], LL = L.l, CLAVE = 'planear-lista-v1';
  var guardado = {};
  try { guardado = JSON.parse(localStorage.getItem(CLAVE) || '{}'); } catch (e) { guardado = {}; }
  var lServicio = guardado._svc || 'consultorio';
  var lFrances = !!guardado._fr;
  var cajaLista = h('div', { class: 'pl-list' });
  P2.appendChild(cajaLista);
  function guardar() { try { guardado._svc = lServicio; guardado._fr = lFrances; localStorage.setItem(CLAVE, JSON.stringify(guardado)); } catch (e) { /* sin almacenamiento */ } }
  function dibujarLista() {
    cajaLista.innerHTML = '';
    cajaLista.appendChild(campo(LL.servicio, chips(LL.servicio, ['consultorio', 'hotel', 'domicilio', 'teleconsulta'].map(function (k) { return { v: k, t: L.svc[k] }; }), lServicio, function (v) { lServicio = v; guardar(); dibujarLista(); })));
    cajaLista.appendChild(casilla(LL.frances, lFrances, function (v) { lFrances = v; guardar(); dibujarLista(); }));
    var items = LL.comun.concat(LL[lServicio]);
    var conFr = lFrances && (lServicio === 'consultorio' || lServicio === 'hotel');
    if (conFr) items = items.concat([LL.fr]);
    var anillo = h('div', { class: 'pl-ring' }, [h('span', { class: 'pl-ring-n' })]);
    var ul = h('ul', { class: 'pl-items' });
    function actualizar() {
      var hechos = items.filter(function (it) { return guardado[lServicio + ':' + it[0]]; }).length;
      var pct = Math.round(hechos / items.length * 100);
      anillo.style.setProperty('--p', pct);
      anillo.firstChild.textContent = pct + '%';
      cajaLista.classList.toggle('pl-done', hechos === items.length);
    }
    items.forEach(function (it) {
      var clave = lServicio + ':' + it[0];
      var c = casilla(it[1], !!guardado[clave], function (v) { guardado[clave] = v; guardar(); actualizar(); });
      if (it[2]) c.querySelector('label').appendChild(h('a', { href: it[2], class: 'pl-link', text: ' →' }));
      ul.appendChild(h('li', {}, [c]));
    });
    cajaLista.appendChild(h('div', { class: 'pl-list-head' }, [h('h3', { class: 'pl-q', text: LL.titulo }), anillo]));
    if (lFrances && !conFr) cajaLista.appendChild(h('p', { class: 'pl-note', text: LL.frNo }));
    cajaLista.appendChild(ul);
    cajaLista.appendChild(h('p', { class: 'pl-done-msg', text: LL.listo }));
    cajaLista.appendChild(h('p', { class: 'pl-note', text: LL.local }));
    var texto = function () {
      return LL.compartirT.replace('{s}', L.svc[lServicio]) + '\n' + items.map(function (it) { return (guardado[lServicio + ':' + it[0]] ? '✅ ' : '⬜ ') + it[1]; }).join('\n') + '\n' + LL.compartirF;
    };
    var aviso = h('span', { class: 'pl-note', role: 'status' });
    cajaLista.appendChild(h('div', { class: 'pl-actions' }, [
      h('a', { class: 'hero-cta', href: '#', text: LL.enviar, onclick: function (e) { e.preventDefault(); window.open('https://wa.me/?text=' + encodeURIComponent(texto()), '_blank', 'noopener'); } }),
      h('button', { type: 'button', class: 'hero-cta ghost', text: LL.copiar, onclick: function () {
        var t = texto();
        (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(function () { aviso.textContent = LL.copiado; }, function () {
          var ta = h('textarea'); ta.value = t; document.body.appendChild(ta); ta.select();
          try { document.execCommand('copy'); aviso.textContent = LL.copiado; } catch (e) { aviso.textContent = ''; }
          ta.remove();
        });
      } }), aviso
    ]));
    cajaLista.appendChild(h('button', { type: 'button', class: 'pl-back', text: LL.borrar, onclick: function () { items.forEach(function (it) { delete guardado[lServicio + ':' + it[0]]; }); guardar(); dibujarLista(); } }));
    actualizar();
  }
  dibujarLista();
  requestAnimationFrame(moverIndicador);

  /* ── buscador de preguntas frecuentes ────── */
  (function () {
    var seccion = document.getElementById('faq'), items = seccion ? seccion.querySelectorAll('.faq-item') : [];
    if (!items.length) return;
    var B = { es: ['Buscar en las preguntas', 'Por ejemplo: hotel, horario, seguro, niños', 'No encontramos esa pregunta.', 'Escríbanos por WhatsApp'],
              en: ['Search the questions', 'For example: hotel, hours, insurance, children', 'We could not find that question.', 'Message us on WhatsApp'],
              fr: ['Rechercher dans les questions', 'Par exemple : hôtel, horaires, assurance, enfants', 'Nous n’avons pas trouvé cette question.', 'Écrivez-nous par WhatsApp'] }[lang] || [];
    var sin = function (t) { return t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); };
    // Sinónimos: lo que el paciente escribe → palabras que sí están en las respuestas.
    var SIN = { es: { nino: ['menor', '15 anos'], ninos: ['menor', '15 anos'], nina: ['menor'], hijo: ['menor'], hija: ['menor'], bebe: ['menor'], embarazo: ['embaraz'], pago: ['anticipo', 'pag', '$'], pagar: ['anticipo', 'pag'], precio: ['$'], precios: ['$'], costo: ['$'], cuesta: ['$'], tarjeta: ['anticipo', 'tarjeta'], cita: ['agend', 'cita'], reservar: ['agend', 'reserv'], llegar: ['llegada', 'tarda'], direccion: ['consultorio'] },
                en: { child: ['under 15'], children: ['under 15'], kid: ['under 15'], kids: ['under 15'], baby: ['under 15'], pregnancy: ['pregnan'], price: ['$'], prices: ['$'], cost: ['$'], payment: ['deposit', 'pay', '$'], pay: ['deposit', 'pay'], appointment: ['book'], address: ['clinic'], arrive: ['reach', 'arrival'] },
                fr: { enfant: ['moins de 15'], enfants: ['moins de 15'], bebe: ['moins de 15'], grossesse: ['enceinte'], prix: ['$'], cout: ['$'], paiement: ['acompte', 'pai', '$'], payer: ['acompte', 'pai'], 'rendez-vous': ['reserv'], adresse: ['cabinet'], arriver: ['arriv'] } }[lang] || {};
    var campo = h('input', { type: 'search', class: 'pl-input pl-faq-input', placeholder: B[1], 'aria-label': B[0] });
    var vacio = h('p', { class: 'pl-empty pl-faq-vacio', hidden: true }, [B[2] + ' ', h('a', { class: 'text-link', href: 'https://wa.me/' + D.whatsapp, target: '_blank', rel: 'noopener', text: B[3] })]);
    var caja = h('div', { class: 'pl-faq-search reveal visible' }, [h('label', { class: 'pl-label', text: B[0] }), campo]);
    seccion.querySelector('.section-header').after(caja);
    items[items.length - 1].parentNode.after(vacio);
    campo.addEventListener('input', function () {
      var q = sin(campo.value.trim()), n = 0;
      Array.prototype.forEach.call(items, function (it) {
        var txt = sin(it.textContent);
        var ok = !q || q.split(/\s+/).every(function (w) { return [w].concat(SIN[w] || []).some(function (x) { return txt.indexOf(sin(x)) >= 0; }); });
        it.hidden = !ok; if (ok) n++;
      });
      vacio.hidden = n > 0;
    });
  })();

  /* ── portada más dinámica ─────────────────── */
  if (!quieto) {
    // Contador del dato principal del hero ("Desde 60 min").
    var dato = document.querySelector('.hero2-facts li strong');
    if (dato) {
      var m = dato.textContent.match(/(\d+)/);
      if (m) {
        var fin = +m[1], antes = dato.textContent.slice(0, m.index), despues = dato.textContent.slice(m.index + m[1].length), t0 = null;
        requestAnimationFrame(function anima(t) {
          if (!t0) t0 = t;
          var p = Math.min(1, (t - t0) / 1100);
          dato.textContent = antes + Math.round(fin * (1 - Math.pow(1 - p, 3))) + despues;
          if (p < 1) requestAnimationFrame(anima);
        });
      }
    }
    // Tarjetas de servicio con inclinación y brillo que siguen al ratón (solo con puntero fino).
    if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      Array.prototype.forEach.call(document.querySelectorAll('.svc-card'), function (c) {
        c.classList.add('pl-tilt');
        c.addEventListener('pointermove', function (e) {
          var r = c.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
          c.style.setProperty('--mx', (x * 100) + '%'); c.style.setProperty('--my', (y * 100) + '%');
          c.style.transform = 'perspective(800px) rotateX(' + ((0.5 - y) * 5) + 'deg) rotateY(' + ((x - 0.5) * 6) + 'deg) translateY(-3px)';
        });
        c.addEventListener('pointerleave', function () { c.style.transform = ''; });
      });
    }
  }

  // Para pruebas automáticas (no afecta a la página).
  /* ── calendario: oculta las fechas que ya pasaron ── */
  (function () {
    var ya = hoy();
    document.querySelectorAll('.schedule-list li[data-hasta]').forEach(function (li) { if (li.getAttribute('data-hasta') < ya) li.hidden = true; });
    document.querySelectorAll('.schedule-card').forEach(function (card) {
      var filas = card.querySelectorAll('.schedule-list li[data-hasta]');
      if (filas.length && !card.querySelector('.schedule-list li[data-hasta]:not([hidden])')) card.hidden = true;
    });
  })();

  window.__planear = { cotizar: cotizar, horario: horario, datos: D };
})();
