🔍 REPORTE DE DEBUGGING RAGAs
============================================================

📊 ANÁLISIS GENERAL DE MÉTRICAS:
   Score combinado - Media: 0.770, Zeros: 5.8%
   faithfulness - Media: 0.734, Zeros: 15.5%
   answer_relevancy - Media: 0.769, Zeros: 15.5%
   context_precision - Media: 0.844, Zeros: 5.8%
   context_recall - Media: 0.831, Zeros: 5.8%
   answer_correctness - Media: 0.727, Zeros: 15.5%
   answer_similarity - Media: 0.674, Zeros: 15.5%

🚨 ANÁLISIS DE STRICTNESS:
   Score de strictness general: 0.136
   Casos con respuestas razonables pero scores bajos: 6

   Ejemplos de posible strictness excesiva:
   1. Q6 - qwen3:32b: Score 0.000
      Respuesta: [Respuesta truncada - solo thinking]...
   2. Q9 - deepseek-r1:latest: Score 0.305
      Respuesta: Para comprar la comida para los desayunos en DNI Valencia, sigue estos pasos:

1. **Punto de encuent...
   3. Q19 - qwen3:32b: Score 0.000
      Respuesta: [Respuesta truncada - solo thinking]...

💡 RECOMENDACIONES:
   1. ⚠️ Hay 6 casos con respuestas razonables pero scores bajos
   2. 💡 Considerar implementar evaluación híbrida que combine RAGAs con análisis cualitativo
   3. 🔧 Para respuestas con scores bajos pero razonables, considerar re-evaluación manual