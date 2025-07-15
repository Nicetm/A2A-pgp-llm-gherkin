import yaml

# Carga el docker-compose.yml
def main():
    with open('docker-compose.yml', 'r', encoding='utf-8') as f:
        compose = yaml.safe_load(f)

    services = compose.get('services', {})

    nodes = []
    edges = []

    for service_name, service in services.items():
        ports = service.get('ports', [])
        port_str = ports[0] if ports else ''
        label = f"{service_name}\\n{service.get('container_name', '')}\\n{port_str}"
        nodes.append(f'    {service_name}["{label}"]')

    # Busca conexiones por depends_on
    for service_name, service in services.items():
        depends = service.get('depends_on', [])
        for dep in depends:
            edges.append(f'    {service_name} --> {dep}')

    with open('arquitectura.mmd', 'w', encoding='utf-8') as f:
        f.write('graph TD\n')
        for node in nodes:
            f.write(node + '\n')
        for edge in edges:
            f.write(edge + '\n')

    print("¡Diagrama Mermaid generado en arquitectura.mmd!")

if __name__ == "__main__":
    main() 