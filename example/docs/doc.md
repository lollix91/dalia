# Emergency Filtering/Evacuation/Response MAS

Title: __Multi-Agent System for Emergency Management in a City or Comune__

## Objective
This Multi agent System follows [**GAIA methodology**](https://link.springer.com/content/pdf/10.1023/A:1010071910869.pdf) in order to implement a Decentralized Emergency Filtering and Evacuation Response System using [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI).

---

## Documentation: 

### 1.1 Roles

| Role         | Main Responsibilities                                     |
|--------------|-----------------------------------------------------------|
| **Sensor**   | Detects ALL anomalies, filters out the Emergency ones (earthquake, fire, smoke), sending out either an alarm or a false-alarm.    |
| **Coordinator** | Coordinates between the other agents, immediately evacuates, requests equipment from the manager, dispatches the responder with the proper equipment. |
| **Evacuator**| evacuates people from the affected location.         |
| **Manager**| Evaluates and dispatches the proper equipment for the emegency type.      |
| **Responder**| uses the equipment to counteract and remedy the emergency at the affected location.                              |
| **Logger**   | Records all events, actions, and system status.           |
| **Communicator**   | sends mass alarms to citizens as a response of being informed by the coordinator of a disaster/emergency           |
| **Person**   | receives a copy of the mass alarms.           |

---

### 1.2 Virtual Organization

- **Name**: `EmergencyFilteringEvacuationResponse`
- **Goals**:
  - Minimize risks to people and infrastructure.
  - Ensure prompt and coordinated reaction to emergencies.
  - Support distributed decision-making among agents.
- **Roles and Interactions**:
  - `Sensor → Coordinator`: sends alarm messages.
  - `Coordinator → Communicator`: informs the communicator of emergency.
  - `Communicator → Person`: sends a mass alarm with the emergency it has been informed with.
  - `Coordinator → Evacuator`: sends evacuation commands.
  - `Coordinator → Manager`: requests equipment.
  - `Manager → Coordinator`: dispatches equipment.
  - `Coordinator → Responder`: sends emergency response command.
  - `Sensor/Coordinator/Manager/Evacuator/Responder → Logger`: record of all relevant events and actions.

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
| `dispense(E)`        | internal | state |


#### Logger

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `generic(E, L)`        | external | agents |
| `alarm(E, L)`        | external | agents |
| `falarm(E, L)`        | external | agents |
| `message(X)`        | external | agents |


#### Communicator

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `communicate(Targets, Content)`        | external | Coordinator |


#### Person

| Event                | Type     | Source      |
|----------------------|----------|-------------|
| `message(Content)`        | external | Communicator |
---

### 1.4 Action Table

#### Sensor

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `log(X)`   | sends events to the Logger           |

#### Coordinator

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `equip(X)`   | sends equipment request to the Manager           |
| `evacuate(X)`   | sends evacuation command to the Evacuator   using the **inform FIPA performative**        |
| `log(X)`   | sends events to the Logger           |


#### Evacuator

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `log(X)`   | sends events to the Logger           |


#### Manager

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `log(X)`   | sends events to the Logger           |


#### Responder

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `log(X)`   | sends events to the Logger           |


#### Communicator

| Action                      | Description                                 |
|-----------------------------|---------------------------------------------|
| `contact(Target, Content)`   | sends Content to a  Target of type Person          |
---

### 1.5 Agent Behaviors

- **Sensor**: Proactive; generates states upon detecting anomalies, filters out alarms from false and informs the coordinator, and Proactive for its use of internal states and events.
- **Coordinator**: reactive to incoming alarms; proactive in managing the response strategy according to incoming equipment, also proactive in manageing its states until it achieve equilibrium (internal event done), and Proactive for its use of internal states and events. uses the **inform FIPA performative** to tell the communicator to mass inform the people in a disaster zone the type of disaster (mass alarm).
- **Evacuator**: reactive to evacuation commands; can report issues or confirmation.
- **Manager**: Proactive by evaluating which equipment belongs to which emergency response, and its use of internal states and events.
- **Responder**: reactive to response commands; can report issues or confirmation.
- **Logger**: reactive; logs every received message or command.
- **Communicator**: hybrid reactive/proactive; receives a list of targets and a message content as a result of an **inform FIPA performative** and maps that content to a message to be mass sent to all targets.
- **Person**: reactive; receives a coppy of the mass message content.

---