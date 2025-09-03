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
    T->>C: arrived(location)
    C->>T: transport(location, away, bystanders, personal_items)
    T->>C: done(transport)
    C->>T: go(base)
    T->>C: arrived(base)
    E->>C: sends(equipment)
    C->>T: transport(base, location, firefighters, equipment)
    T->>C: done(transport)
    C->>F: use(equipment, emergency_type)
    
    Note over E: Dispenses equipment based on emergency type
    E->>L: log_event(equipment_choice)
    
    Note over T: Transports people and equipment
    T->>L: log_event(from_to_who_what)
    
    Note over F: uses the equipment to resolve the emergency type
    F->>L: log_event(equipment_vs_emergency)
    
    Note over L: Records all events
``` 