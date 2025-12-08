# Conclusiones - Entrega 2: Implementación de Pipeline MLOps

## Preguntas del Enunciado

A continuación se responden las preguntas planteadas en el notebook del enunciado, basadas en la experiencia de implementación del proyecto.

### 1. ¿Cómo mejoró el desarrollo del proyecto al utilizar herramientas de tracking y despliegue?

La incorporación de herramientas de tracking como MLflow y de despliegue mediante Docker, Airflow y FastAPI representó un cambio fundamental en cómo el modelo puede ser utilizado en un contexto real. En lugar de tener simplemente un notebook con un modelo entrenado que vive de forma aislada, ahora contamos con un sistema productivo completo.

El cambio más significativo es que ahora el pipeline de Airflow monitorea automáticamente la llegada de nuevos datos, permitiendo detectar cuándo estos datos han cambiado lo suficiente como para justificar un reentrenamiento del modelo. Esta capacidad de detección de drift hace que el sistema trabaje de forma más inteligente, decidiendo por sí mismo cuándo es necesario invertir recursos computacionales en reentrenar y cuándo puede simplemente reutilizar el modelo existente que sigue siendo válido.

Otro aspecto crucial es cómo se amplifica el impacto del modelo. Al desplegarlo como un servicio web con una API REST y una interfaz Gradio, el sistema puede servir predicciones a múltiples usuarios simultáneamente. Esto hace que el modelo tenga un impacto real en el negocio de SodAI Drinks, ya que puede ser integrado directamente en aplicaciones existentes de la empresa o utilizado de forma interactiva por analistas de negocio sin conocimientos técnicos profundos.

MLflow, por su parte, facilitó enormemente la experimentación durante el desarrollo. Poder comparar diferentes versiones del modelo, ver qué hiperparámetros funcionaron mejor, y tener la capacidad de volver a versiones anteriores si fuera necesario, aceleró significativamente el ciclo de mejora continua. El tracking nos dio visibilidad completa sobre qué funciona y qué no, mientras que el despliegue nos permitió llevar esa funcionalidad a usuarios reales que pueden beneficiarse de ella.

### 2. ¿Qué aspectos del despliegue con Gradio/FastAPI fueron más desafiantes o interesantes?

Sin duda, el aspecto más desafiante del despliegue fue lograr la congruencia entre clientes y productos en el frontend. Al principio, el sistema mostraba indiscriminadamente todos los clientes del dataset (1569 en total) y todos los productos disponibles. Sin embargo, esta aproximación no era realista ni útil para el usuario final. Lo que realmente queríamos era una experiencia coherente donde se mostraran únicamente los clientes que tenían historial de transacciones (1490) y, más importante aún, que al seleccionar un cliente específico, se cargaran dinámicamente solo los productos que ese cliente había comprado anteriormente.

Este desafío aparentemente simple resultó ser técnicamente complejo. Primero tuvimos que diseñar endpoints específicos en FastAPI: uno para obtener la lista filtrada de clientes con transacciones, y otro para obtener los productos históricos de cada cliente. Luego vino el problema de los tipos de datos, ya que los identificadores de clientes y productos son int64 en los DataFrames de Pandas, pero llegan como strings desde la URL del endpoint HTTP. Fue necesario manejar explícitamente estas conversiones para evitar errores de comparación.

La parte de Gradio también tuvo su complejidad. Implementamos lógica de actualización dinámica donde el dropdown de productos se recarga automáticamente cada vez que el usuario selecciona un cliente diferente, mostrando solo las opciones relevantes. Finalmente, tuvimos que asegurar que los volúmenes compartidos entre el contenedor de Airflow y el backend funcionaran correctamente, permitiendo que el backend accediera a los datos de transacciones generados por el pipeline.

Una vez resueltos estos desafíos, el resultado fue muy satisfactorio: una interfaz intuitiva donde el usuario ve únicamente opciones válidas y puede obtener predicciones de manera natural, sin confusión ni opciones irrelevantes.

Otro aspecto particularmente interesante fue decidir entre una arquitectura de predicciones pre-calculadas versus predicciones en tiempo real. Optamos por la primera: el pipeline de Airflow genera todas las predicciones posibles de antemano para todas las combinaciones cliente-producto, y el frontend simplemente consulta estas predicciones ya calculadas. Esta decisión arquitectónica hace que las respuestas sean prácticamente instantáneas para el usuario, a diferencia de un sistema que necesitaría invocar el modelo y procesar features cada vez que se solicita una predicción.

### 3. ¿Cómo aporta Airflow a la robustez y escalabilidad del pipeline?

Apache Airflow ha sido fundamental para hacer el pipeline robusto y escalable, aportando valor en múltiples dimensiones que van más allá de simplemente ejecutar scripts en secuencia.

En cuanto a robustez, la visualización gráfica del DAG es invaluable. Poder ver todas las etapas del pipeline y sus dependencias de forma visual hace que sea extremadamente fácil identificar dónde ocurrió un problema cuando algo falla. Airflow no solo detecta las fallas automáticamente, sino que registra cada error con contexto completo y puede configurarse para reintentar tareas automáticamente o enviar alertas a los responsables del sistema.

Los logs centralizados son otro aspecto crucial de la robustez. Cada tarea genera logs detallados que son accesibles directamente desde la interfaz web, eliminando la necesidad de conectarse a servidores remotos o buscar archivos de log dispersos en diferentes ubicaciones. Esto acelera enormemente el proceso de debugging cuando algo no funciona como se esperaba. Además, las tareas pueden diseñarse para ser idempotentes, lo que significa que pueden re-ejecutarse múltiples veces sin causar efectos secundarios indeseados, una propiedad esencial para sistemas productivos confiables.

Desde el punto de vista de escalabilidad, Airflow brilla por su capacidad de procesamiento distribuido. El sistema puede ejecutar tareas en paralelo y distribuir la carga entre múltiples workers, algo absolutamente crucial cuando el volumen de datos crece. Conforme SodAI Drinks expanda sus operaciones, el pipeline puede crecer horizontalmente agregando más workers sin necesidad de rediseñar la arquitectura.

La programación flexible es otro punto fuerte. Airflow permite definir con precisión cuándo y con qué frecuencia ejecutar el pipeline: puede ser diariamente, semanalmente, o incluso disparado por eventos específicos como la llegada de nuevos datos. Esta flexibilidad permite adaptar el sistema a las necesidades cambiantes del negocio sin modificar el código core del pipeline.

Finalmente, la reutilización de código que promueve Airflow acelera el desarrollo de nuevos pipelines. Los DAGs y operadores pueden adaptarse fácilmente para diferentes proyectos, evitando tener que reinventar la rueda cada vez.

En resumen, Airflow transforma lo que sería una arquitectura de datos compleja y opaca en un sistema legible, mantenible y accesible, tanto para desarrolladores como para usuarios de negocio que necesitan monitorear el estado del sistema. Sin una herramienta de orquestación como esta, gestionar manualmente scripts de Python que dependen unos de otros sería extremadamente propenso a errores y prácticamente imposible de escalar de manera eficiente.

### 4. ¿Qué se podría mejorar en una versión futura del flujo? ¿Qué partes automatizarían más, qué monitorearían o qué métricas agregarían?

Aunque el sistema actual funciona bien, hay varias áreas donde podríamos llevar la automatización y el monitoreo al siguiente nivel.

En el frente de automatización, una mejora prioritaria sería implementar un sistema de alertas automáticas que notifique al equipo por email o Slack cuando se detecte drift, cuando falle una tarea crítica, o cuando el desempeño del modelo caiga por debajo de umbrales definidos. Actualmente, aunque el sistema detecta estos eventos, requiere que alguien revise la interfaz de Airflow proactivamente. También sería valioso automatizar el re-deployment del modelo: cuando se entrena una nueva versión que mejora significativamente a la anterior, el sistema debería promoverla automáticamente a producción en lugar de requerir intervención manual como ocurre ahora.

Otra mejora sería implementar sensores de Airflow que detecten automáticamente la llegada de nuevos archivos de datos y disparen el pipeline inmediatamente, en lugar de depender de un calendario fijo. Esto haría el sistema más reactivo a los datos del negocio. Para manejar cargas variables de trabajo, podríamos integrar Kubernetes para escalar automáticamente el número de workers de Airflow según la demanda.

El monitoreo también tiene espacio para crecer significativamente. Lo más importante sería implementar un feedback loop donde comparemos las predicciones con los resultados reales una vez que estén disponibles, calculando métricas en vivo como degradación de accuracy. Esto nos permitiría detectar problemas de performance antes de que se vuelvan críticos. También deberíamos agregar validaciones automáticas de calidad de datos que verifiquen valores faltantes, outliers extremos, y distribuciones anómalas antes de usar los datos para predicción.

En cuanto a métricas, actualmente nos enfocamos principalmente en métricas técnicas como F1-Score y ROC-AUC. Sin embargo, sería muy valioso incorporar métricas de negocio específicas como "ahorro logístico estimado" o "tasa de conversión de predicciones" que hablen directamente al valor que el modelo genera para SodAI Drinks. También deberíamos monitorear fairness metrics para asegurar que el modelo no discrimine injustamente entre diferentes tipos de clientes, por ejemplo entre ABARROTES y MAYORISTA.

Un aspecto particularmente interesante sería monitorear no solo el drift en los valores de las features, sino también el drift en la importancia de las features. Usando SHAP values a lo largo del tiempo, podríamos detectar si las variables que el modelo considera importantes están cambiando, lo cual podría indicar cambios fundamentales en el comportamiento de compra.

Para experimentación avanzada, implementar un framework de A/B testing permitiría que convivieran dos versiones del modelo en producción, dirigiendo un porcentaje del tráfico a cada una y comparando su desempeño real antes de decidir cuál mantener. También sería valioso crear un feature store centralizado que gestione las features calculadas, permitiendo reutilizarlas entre diferentes modelos y asegurando consistencia entre el entrenamiento y la inferencia.

Finalmente, en lugar de reentrenar todo desde cero cada vez, podríamos explorar técnicas de incremental learning o continuous training que actualicen el modelo con datos nuevos sin perder el conocimiento adquirido previamente. Esto podría ser más eficiente computacionalmente y permitir que el modelo se adapte más rápidamente a cambios graduales en los patrones de compra.

En términos de interfaz de usuario, crear un dashboard ejecutivo con Streamlit o Dash mostraría métricas clave del negocio, tendencias de predicciones y alertas en tiempo real de forma más visual que la interfaz actual. También sería útil mostrar en Gradio no solo la predicción, sino también qué features fueron más influyentes usando gráficos SHAP, ayudando a los usuarios a entender por qué el modelo predice lo que predice y generando mayor confianza en las recomendaciones del sistema.

## 9. Conclusión Final

Este proyecto demuestra la implementación exitosa de un sistema MLOps end-to-end que automatiza todo el ciclo de vida de un modelo de machine learning, desde la ingesta de datos hasta el serving de predicciones a usuarios finales.

Los componentes integrados del sistema proporcionan:

- **Automatización inteligente**: El pipeline de Airflow ejecuta reentrenamiento condicional basado en drift detection, optimizando recursos mientras mantiene la calidad del modelo
- **Reproducibilidad y trazabilidad**: MLflow registra cada experimento, permitiendo auditoría completa y comparación histórica de modelos
- **Accesibilidad**: La API REST y la interfaz Gradio democratizan el acceso a las predicciones, tanto para integraciones programáticas como para usuarios no técnicos
- **Mantenibilidad**: La arquitectura containerizada y el código modular facilitan actualizaciones y debugging
- **Escalabilidad**: El sistema está preparado para crecer, tanto en volumen de datos como en número de usuarios

El modelo alcanza métricas sólidas (F1-Score: 0.8646, ROC-AUC: 0.9695), demostrando que es capaz de identificar con alta precisión qué clientes comprarán productos específicos en la siguiente semana. Más importante aún, este modelo no existe aislado en un notebook, sino que opera como un **servicio productivo** que puede generar valor real para SodAI Drinks, optimizando su cadena de suministro y mejorando la gestión de inventario.

La implementación de este pipeline MLOps representa un paso fundamental en la transformación de ciencia de datos experimental en ingeniería de datos productiva y confiable.




--------------------------------------------------------------------------




---

## Descripción Técnica del Proyecto

### 1. Resumen Ejecutivo

En esta segunda entrega se desarrolló un pipeline MLOps completo para el sistema de predicción de pedidos de SodAI Drinks. El proyecto representa la evolución del modelo de machine learning desarrollado en la entrega anterior, transformándolo de un experimento aislado en un notebook a un sistema productivo completo.

El ecosistema integra orquestación de flujos de trabajo mediante Apache Airflow, experimentación y trazabilidad con MLflow, monitoreo inteligente con detección automática de data drift, un servicio de predicciones accesible a través de una API REST desarrollada con FastAPI, y una interfaz de usuario interactiva construida con Gradio. Todo esto desplegado sobre una infraestructura containerizada con Docker que garantiza portabilidad y reproducibilidad.

Lo que hace especial a esta arquitectura es que permite que el modelo predictivo no solo funcione de manera aislada en un ambiente de desarrollo, sino que opere como un servicio productivo real, escalable y mantenible, listo para generar valor en un contexto empresarial.

### 2. Modelo de Machine Learning

Para abordar el problema de predicción de compras se seleccionó LightGBM, un algoritmo de gradient boosting reconocido por su eficiencia computacional y capacidad de manejar datasets grandes manteniendo alta precisión. La elección de este algoritmo se fundamentó en su capacidad de capturar relaciones no lineales complejas entre las variables y su velocidad de entrenamiento, aspectos cruciales cuando se trabaja con el producto cartesiano de clientes y productos.

Un desafío importante del dataset es el desbalanceo de clases inherente al problema: no todos los clientes compran todos los productos cada semana, lo que resulta en significativamente más ejemplos negativos que positivos. Para mitigar este problema se implementó SMOTE (Synthetic Minority Over-sampling Technique), una técnica que genera ejemplos sintéticos de la clase minoritaria mediante interpolación, permitiendo que el modelo aprenda mejor los patrones de compra sin simplemente memorizar la clase mayoritaria.

La optimización de hiperparámetros se realizó mediante Optuna, una librería que utiliza búsqueda bayesiana inteligente. A diferencia de métodos tradicionales como grid search que prueban todas las combinaciones posibles, Optuna aprende de los trials anteriores para proponer configuraciones más prometedoras. Con 25 trials, el sistema encontró una configuración óptima que balancea precisión con tiempo de entrenamiento: una tasa de aprendizaje conservadora de 0.0178 para evitar overfitting, 238 árboles en el ensemble, 203 hojas por árbol para capturar complejidad, profundidad máxima de 11 para controlar el overfitting, un mínimo de 7 muestras por hoja para regularización, y utilización del 64.96% de las features en cada iteración (similar a la técnica de random forest).

El modelo entrenado alcanzó un F1-Score de 0.8646, indicando un excelente balance entre precisión y recall. El ROC-AUC de 0.9695 demuestra una capacidad sobresaliente de discriminación entre clases, mientras que el PR-AUC de 0.9222 confirma que el modelo mantiene alto desempeño incluso en el contexto de clases desbalanceadas. Con una precisión de 83.15%, el modelo asegura que la mayoría de las predicciones positivas son correctas, minimizando falsos positivos que podrían llevar a sobrestimar la demanda. El recall de 90.03% indica que el modelo captura la gran mayoría de las compras reales, crucial para no perder oportunidades de venta.

Estas métricas demuestran que el modelo es capaz de identificar con alta confiabilidad qué clientes comprarán productos específicos en la siguiente semana, permitiendo a SodAI Drinks optimizar su logística, reducir desperdicio de inventario, y mejorar la satisfacción del cliente mediante mejor disponibilidad de productos.

### 3. Pipeline de Apache Airflow

El corazón del sistema es un DAG (Directed Acyclic Graph) de Airflow que orquesta el flujo completo de datos y modelo. El pipeline comienza con la extracción de datos desde archivos parquet que contienen información de clientes, productos y transacciones. Esta primera etapa asegura que todos los datos necesarios estén disponibles y correctamente versionados.

La transformación de datos es donde ocurre la mayor parte de la ingeniería de features. El sistema agrega las transacciones semanalmente, crea el producto cartesiano de todas las combinaciones cliente-producto-semana posibles, y calcula features temporales sofisticadas como lags (compras de t-1 y t-2 semanas atrás), promedios móviles de 4 semanas, e indicadores de compra reciente. Estas features temporales son cruciales porque capturan patrones de recompra y estacionalidad en el comportamiento de compra.

Una característica distintiva del pipeline es su capacidad de detectar automáticamente data drift. Después de la transformación, el sistema calcula estadísticas descriptivas de todas las features numéricas y las compara con las estadísticas históricas almacenadas de ejecuciones anteriores. Si los z-scores de estas comparaciones exceden 2.0 en alguna variable, el sistema concluye que los datos han cambiado significativamente y dispara un reentrenamiento completo del modelo.

Este reentrenamiento condicional, implementado mediante un `BranchPythonOperator`, es clave para la eficiencia del sistema. En lugar de reentrenar el modelo costosamente en cada ejecución semanal, el sistema es lo suficientemente inteligente para reutilizar el modelo existente cuando los patrones de datos permanecen estables. Solo cuando detecta cambios reales en las distribuciones invierte recursos en reoptimizar hiperparámetros y reentrenar desde cero.

Finalmente, el pipeline genera predicciones para todas las combinaciones cliente-producto de la semana siguiente, utilizando ya sea el modelo recién entrenado o el existente según lo determinó la etapa de drift detection. Estas predicciones se almacenan en formato parquet con timestamp, creando un registro histórico que puede ser analizado posteriormente.

### 4. Tracking de Experimentos con MLflow

MLflow se integró al pipeline para proporcionar trazabilidad completa de todos los experimentos de machine learning. Cada vez que el sistema reentrena el modelo, MLflow registra automáticamente todos los hiperparámetros utilizados, las métricas de desempeño obtenidas (F1-Score, ROC-AUC, PR-AUC, Precision, Recall), y artefactos importantes como el modelo serializado, gráficos SHAP de interpretabilidad, y la matriz de confusión.

Esta integración aporta beneficios fundamentales para el ciclo de vida del modelo. Cada versión queda completamente documentada, permitiendo comparar fácilmente el desempeño de diferentes configuraciones a través del tiempo. Si en algún momento necesitamos volver a una versión anterior del modelo, podemos hacerlo con confianza porque tenemos todos los parámetros exactos y el contexto de por qué ese modelo funcionó de cierta manera. Para organizaciones que requieren auditorías o cumplimiento regulatorio, tener este historial completo de todos los modelos entrenados es invaluable.

### 5. Servicio de Predicciones: Aplicación Web

El modelo se expone a través de una arquitectura cliente-servidor moderna. El backend, construido con FastAPI, proporciona una API REST completa con endpoints para consultar clientes disponibles, obtener productos históricos de cada cliente, consultar predicciones específicas, generar predicciones en tiempo real para features arbitrarias, procesar predicciones en lote, y obtener el ranking de las mejores oportunidades de venta. La API incluye también endpoints de health check y metadatos del modelo para facilitar el monitoreo y la integración con sistemas de alertas.

Un aspecto clave del diseño es que la API carga automáticamente el modelo entrenado y las predicciones pre-calculadas al iniciar, utilizando volúmenes compartidos de Docker con el contenedor de Airflow. Esto asegura que siempre está sirviendo las predicciones más recientes sin necesidad de intervención manual.

El frontend, desarrollado con Gradio, ofrece una interfaz intuitiva para usuarios no técnicos. La característica más útil es la selección dinámica: cuando el usuario elige un cliente del dropdown, automáticamente se cargan solo los productos que ese cliente ha comprado históricamente, evitando confusión con combinaciones irrelevantes. Los resultados se presentan de forma clara mostrando si el cliente comprará o no, con la probabilidad asociada y la fecha para la cual se hizo la predicción. La interfaz también incluye una pestaña de "Top Predicciones" que muestra las mejores oportunidades de venta, útil para priorizar esfuerzos comerciales.

Esta arquitectura dual permite que el modelo sea accesible tanto para integraciones programáticas (otras aplicaciones pueden consumir la API) como para usuarios finales que prefieren una interfaz gráfica.

### 6. Infraestructura Containerizada con Docker

Todo el proyecto se desplegó completamente en contenedores Docker, garantizando portabilidad y reproducibilidad. El sistema consta de seis contenedores trabajando en conjunto: tres para Airflow (webserver para la interfaz web, scheduler para orquestar las ejecuciones, y worker para procesar las tareas), uno para PostgreSQL que almacena el estado de Airflow, uno para el backend FastAPI, y uno para el frontend Gradio.

La clave de esta arquitectura es el sistema de volúmenes compartidos que permite la comunicación entre componentes. El directorio de modelos entrenados por Airflow se monta como read-only en el contenedor del backend, asegurando que siempre use la versión más reciente sin posibilidad de corrupción accidental. De manera similar, el directorio de datos con las predicciones generadas es accesible por ambos sistemas. Los DAGs y scripts de Airflow se montan en modo desarrollo, permitiendo modificaciones sin necesidad de reconstruir contenedores cada vez, acelerando el ciclo de desarrollo.

Esta arquitectura permite que un modelo entrenado por el pipeline de Airflow sea automáticamente utilizado por el servicio de predicciones segundos después, sin transferencias manuales, copias de archivos, o reinicios de servicios.

### 7. Lecciones Aprendidas

Durante la implementación surgieron varios desafíos técnicos instructivos. La gestión de dependencias en Python resultó más compleja de lo anticipado, con incompatibilidades entre versiones de NumPy, Pandas y scikit-learn que solo se resolvieron fijando versiones exactas en requirements.txt. LightGBM añadió otra capa de complejidad al requerir la librería de sistema libgomp1 (OpenMP) que no viene en las imágenes slim de Python, obligándonos a modificar el Dockerfile para instalarla explícitamente.

El mapeo de volúmenes en Docker también presentó desafíos sutiles, especialmente al compartir modelos entre contenedores. Las rutas relativas causaban problemas difíciles de debuggear, lo que nos llevó a adoptar rutas absolutas y permisos read-only consistentemente. Como se mencionó anteriormente, la sincronización cliente-producto en el frontend fue particularmente desafiante, requiriendo endpoints personalizados y manejo cuidadoso de conversiones de tipos entre int64 de Pandas y strings de HTTP.

A partir de estos desafíos, se consolidaron varias buenas prácticas. El código se modularizó claramente separando procesamiento de datos, entrenamiento y predicción. Toda configuración sensible se externalizó a variables de entorno evitando hardcoding. Se implementaron health checks en todos los servicios para facilitar monitoreo. El logging estructurado en cada etapa del pipeline aceleró significativamente el debugging cuando surgían problemas. MLflow proporcionó el versionamiento tanto de código como de modelos, creando una red de seguridad invaluable.

