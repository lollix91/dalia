```mermaid
sequenceDiagram
    participant S as Sensor
    participant C as Coordinator
    participant E as EquipmentManager
    participant F as FireFighter
    participant T as Transporter
    participant L as Logger

    Note over S: Detects environmental anomaly
    S->>C: alarm(emergency_type)
    S->>L: log_event(detection)
    
    Note over C: Evaluates severity
    C->>E: request_equipment(emergency_type)
    C->>T: go(location)
    C->>T: transport(location, away, bystanders, personal_items)
    C->>T: go(base)
    C->>T: transport(base, location, firefighters, equipment)
    C->>F: use(equipment, emergency_type)
    
    Note over E: Dispenses equipment based on emergency type
    E->>C: sends(equipment)
    E->>L: log_event(equipment_choice)
    
    Note over T: Transports people and equipment
    T->>L: log_event(from_to_who_what)
    
    Note over F: uses the equipment to resolve the emergency type
    T->>L: log_event(equipment_vs_emergency)
    
    Note over L: Records all events
``` 