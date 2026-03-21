.PHONY: check-env diagrams diagram-dot diagram-diagrams clean-diagrams

UV ?= uv

check-env:
	@echo "Verificando herramientas..."
	@command -v $(UV) >/dev/null || (echo "Error: uv no está instalado" && exit 1)
	@command -v dot >/dev/null || (echo "Error: dot (Graphviz) no está instalado" && exit 1)
	@$(UV) --version
	@$(UV) run python --version
	@dot -V

diagrams: check-env diagram-dot diagram-diagrams

diagram-dot:
	dot -Tpng docs/diagrams/tsp_flow.dot -o docs/diagrams/tsp_flow.png
	dot -Tsvg docs/diagrams/tsp_flow.dot -o docs/diagrams/tsp_flow.svg

diagram-diagrams:
	$(UV) run python docs/diagrams/tsp_flow.py

clean-diagrams:
	rm -f docs/diagrams/tsp_flow.png docs/diagrams/tsp_flow.svg docs/diagrams/tsp_flow_diagrams.png
