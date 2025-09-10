# Emergency Filtering-Evacuation-Response

Title: __Multi-Agent System for Emergency Management in a City or Comune__

## Objective
This Multi agent System follows [**GAIA methodology**](https://link.springer.com/content/pdf/10.1023/A:1010071910869.pdf) in order to implement a Decentralized Emergency Filtering and Evacuation Response System using [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI).

---

## Phase 1: 

### 1.1 Roles

| Role         | Main Responsibilities                                     |
|--------------|-----------------------------------------------------------|
| **Sensor**   | Detects ALL anomalies, filters out the Emergency ones (earthquake, fire, smoke), sending out either an alarm or a false-alarm.    |
| **Coordinator** | Coordinates between the other agents, immediately evacuates, requests equipment from the manager, dispatches the responder with the proper equipment. |
| **Evacuator**| evacuates people from the affected location.         |
| **Manager**| Evaluates and dispatches the proper equipment for the emegency type.      |
| **Responder**| uses the equipment to counteract and remedy the emergency at the affected location.                              |
| **Logger**   | Records all events, actions, and system status.           |

---

### 1.2 Virtual Organization

- **Name**: `EmergencyFilteringEvacuationResponse`
- **Goals**:
  - Minimize risks to people and infrastructure.
  - Ensure prompt and coordinated reaction to emergencies.
  - Support distributed decision-making among agents.
- **Roles and Interactions**:
  - `Sensor → Coordinator`: sends alarm messages.
  - `Coordinator → Evacuator`: sends evacuation commands.
  - `Coordinator → Manager`: requests equipment.
  - `Manager → Coordinator`: dispatches equipment.
  - `Coordinator → Responder`: sends emergency response command.
  - `All → Logger`: record of all relevant events and actions.

---

### 1.3 Event Table

#### Sensor

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `sense(X)`        | external | environment |
| `alarms(X)`        | internal | state |
| `falarms(X)`        | internal | state |

#### Coordinator

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `alarm(X)`           | external | Sensor      |
| `equipped(E)`           | external | Manager      |
| `evacuated(L)`           | external | Evacuator      |
| `responded(L)`           | external | Responder      |
| `response(E, L)`           | internal | state      |
| `done(L)`               | internal | state   |


#### Evacuator

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `evacuate(X)`        | external | Coordinator |


#### Responder

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `respond(L)`        | external | Coordinator |


#### Manager

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `emergency(E)`        | external | Coordinator |


#### Logger

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `generic(E, L)`        | external | agents |
| `alarm(E, L)`        | external | agents |
| `falarm(E, L)`        | external | agents |
| `message(X)`        | external | agents |
---

### 1.4 Action Table

#### Sensor

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `report(X)`   | sends events to the Logger           |

#### Coordinator

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `report(X)`   | sends events to the Logger           |
| `equip(X)`   | sends equipment request to the Manager           |
| `evacuate(X)`   | sends evacuation command to the Evacuator           |


#### Evacuator

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `report(X)`   | sends events to the Logger           |
---

### 1.5 Agent Behaviors

- **Sensor**: Proactive; generates states upon detecting anomalies, filters out alarms from false and informs the coordinator.
- **Coordinator**: reactive to incoming alarms; proactive in managing the response strategy according to incoming equipment, also proactive in manageing its states until it achieve equilibrium (internal event done).
- **Evacuator**: reactive to evacuation commands; can report issues or confirmation.
- **Manager**: Proactive by evaluating which equipment belongs to which emergency response.
- **Responder**: reactive to response commands; can report issues or confirmation.
- **Logger**: reactive; logs every received message or command.

---