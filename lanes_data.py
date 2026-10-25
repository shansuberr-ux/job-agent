# lanes_data.py

STYLE_GUIDE = """
Use a confident, reflective, and highly technical tone that blends engineering precision with a narrative flow. 
Favor active, sophisticated verbs (e.g., 'recursively navigated,' 'honed,' 'streamlined') and focus heavily on the 'how' and 'why' of problem-solving, 
particularly how designs balance theoretical optimization with real-world constraints like manufacturing lead times, tolerances, and cost. 
Avoid excessive, flowery adjectives; let concrete engineering metrics (8 products, 90% FAI pass rate, 135+ radome profiles, 80% vibration correlation, IP68, 6°C thermal reduction), software tools (ANSYS, SolidWorks, Fluent), and manufacturing realities drive the impact.
"""

PRIMARY_LOCATIONS = ["hyderabad", "bangalore", "bengaluru", "chennai", "pune", "remote", "hybrid", "kerala", "thiruvananthapuram", "kochi"]

TARGET_TITLES = [
    "mechanical design engineer", "design engineer", "product design engineer", 
    "npd engineer", "npi engineer", "r&d engineer", "mechanical engineer ii", 
    "mechanical engineer iii", "electromechanical", "enclosure design", 
    "mechanical packaging", "hardware engineer", "cae engineer", "fea engineer", 
    "simulation engineer", "structural analysis", "cfd engineer", 
    "vibration engineer", "stress engineer", "structures engineer"
]

LANES = {
    "sensors": {
        "name": "Sensors / ADAS",
        "resume": "Shan_resume_sensors.pdf",
        "targets": ["Bosch", "Continental", "Valeo", "Aptiv", "Mercedes-Benz", "Capgemini", "ZF", "HELLA", "Forvia", "Magna", "Harman", "Visteon", "Infineon"],
        "subject": "Mechanical Design Engineer, {company}: radar sensor enclosures, IP sealing, thermal",
        "note_template": """Hi {name},

Your role asks for {jd_hook}. At Uhnder I developed two automotive radar chassis and radomes rated IP68 (IEC 60529), cut internal temperature by 6 degrees C by redesigning the fins, and lowered radome cost by 8% without hurting dielectric performance. At JMA Wireless I own NPD and NPI for eight 5G antenna products, with vibration analysis that correlated 80% first-pass to physical tests.

My gap is automotive-specific process work: DFMEA/APQP documentation and NX. I want to return to automotive sensing because my best work was on radar housings, and your program is at a larger scale.

Resume attached. Could we speak for 15 minutes this week?

Shan""",
        "revise": "• IP ratings (IP67, IP6K9K) & gaskets/welds/vents\n• Tolerance stack-up: worst-case vs RSS (radome example)\n• GD&T basics: datums, position, flatness\n• Fin & heat-path thermal basics (6°C reduction)\n• IEC 60068 vibration & drop correlation",
        "learn": "• DFMEA, APQP, PPAP basics\n• NX or CATIA intro\n• ISO 16750 & ISO 20653 scope\n• Radome materials: dielectric constant & loss tangent"
    },
    "defence": {
        "name": "Defence / Radar Hardware",
        "resume": "Shan_resume_defence.pdf",
        "targets": ["Thales", "Data Patterns", "Astra Microwave", "BEL", "Bharat Electronics", "Tata Advanced Systems", "Nokia", "Ericsson", "Rohde & Schwarz", "CommScope", "Keysight", "Tejas"],
        "subject": "Mechanical Design Engineer, {company}: rugged radar and RF hardware",
        "note_template": """Hi {name},

I saw {company} is hiring for {title}. The posting asks for {jd_hook}. I have designed IP68 radar chassis, run harmonic and random vibration analysis that correlated 80% first-pass to test, and qualified antenna products to IEC 60068 vibration and drop standards. I own change control through PLM and supported contract-manufacturer setup in Chennai.

My qualification work was to IEC 60068 at commercial levels, not MIL-STD-810 or 461. I want to move into defence/RF electronics because the engineering rigor is higher and the radar/antenna work matches what I have done.

Resume attached. Could we talk for 15 minutes?

Shan""",
        "revise": "• Random vibration: PSD, Grms vs sine\n• Shock: half-sine pulse, 11 ms, 50 m/s² (~5g)\n• Thermal paths in sealed enclosures; conduction cooling\n• Factor of safety (1.5 to 3 for metals)\n• IEC 60068 vs MIL-STD-810 levels",
        "learn": "• MIL-STD-810H methods 501, 502, 507, 509, 514, 516\n• MIL-STD-461 basics: shielding, gasketing, grounding\n• Connector and RF interface design basics"
    },
    "cae": {
        "name": "CAE / Structural Simulation",
        "resume": "Shan_resume_cae.pdf",
        "targets": ["Tata Elxsi", "KPIT", "L&T Technology Services", "LTTS", "Cyient", "Altair", "Siemens", "Cummins", "Ansys", "Synopsys", "Dassault", "Quest Global", "Capgemini"],
        "subject": "CAE Engineer, {company}: vibration, non-linear FEA and test correlation",
        "note_template": """Hi {name},

Your posting asks for {jd_hook}. I run harmonic and random vibration analysis (IEC 60068-2-6/64) with 80% first-pass correlation to physical tests, non-linear snap-fit analysis that predicted 38 N insertion and 30 N removal force, and Ansys Fluent design-of-experiments on 135+ radome profiles for 12 to 18% wind load reduction.

My gaps are fatigue (S-N, nCode) and HyperMesh/ANSA preprocessing. I enjoy the analysis side of my work most and want a role where CAE is the whole job, across more product types.

Resume attached. Could we speak for 15 minutes?

Shan""",
        "revise": "• Modal, harmonic & random vibration theory; PSD & damping\n• Mesh convergence, contact definitions, boundary conditions\n• Non-linear convergence: large deformation, plasticity, contact stiffness\n• 80% correlation measurement & what the 20% miss taught you\n• DOE structure for 135+ profiles (12-18% wind load reduction)",
        "learn": "• Fatigue: S-N curves, Goodman, stress concentration; nCode basics\n• HyperMesh or ANSA meshing workflow\n• Explicit dynamics (LS-DYNA) for drop simulation\n• PyAnsys scripting"
    },
    "aerospace": {
        "name": "Aerospace / Stress Analysis",
        "resume": "Shan_resume_aerospace.pdf",
        "targets": ["Collins Aerospace", "Honeywell", "Safran", "GE Aerospace", "Airbus", "Tata Advanced Systems", "Skyroot", "Dhruva Space", "Agnikul", "Digantara", "Pixxel", "Sarla Aviation", "ePlane"],
        "subject": "Stress / Structures Engineer, {company}",
        "note_template": """Hi {name},

The role asks for {jd_hook}. I run static structural analysis to factor-of-safety targets of 1.5 to 3 for metals and 2 to 5 for plastics, vibration analysis with 80% first-pass test correlation, and non-linear contact analysis. I back results with my own Excel hand-calculation tools for drag force, crimping force and snap-joint behavior, and I optimized radome aerodynamics in Ansys Fluent over 135+ profiles.

What I lack is aerospace-specific fatigue and damage-tolerance practice and certification standards. I am moving into aerospace because the structural analysis I like most is done most rigorously here.

Resume attached. Could we talk for 15 minutes?

Shan""",
        "revise": "• Hand calculations: beams, plates, bolted joints, margin of safety\n• Buckling and stress concentration factors\n• Vibration: natural frequency checks against hand estimates\n• Drop and vibration test setups",
        "learn": "• Fatigue and damage tolerance fundamentals\n• Material allowables (MMPDS) and joint analysis\n• AS9100 and NADCAP awareness\n• Composite basics"
    },
    "ev": {
        "name": "EV / Mobility",
        "resume": "Shan_resume_ev.pdf",
        "targets": ["Exponent Energy", "Ather", "Ultraviolette", "Simple Energy", "Hero", "TVS", "Ola Electric", "Bajaj Auto", "Mahindra", "Tata Motors", "Raptee"],
        "subject": "Mechanical Design Engineer, {company}: IP-rated enclosures, thermal, DFM",
        "note_template": """Hi {name},

Your role asks for {jd_hook}. That is my last four years: I released sheet-metal, die-cast and molded parts for eight 5G antenna products at a 90% FAI pass rate, designed IP68 radar chassis at Uhnder, and cut internal temperature by 6 degrees C through fin redesign.

My gap is EV-specific: formal DFMEA/DVP documentation and battery standards such as AIS-156. I am moving into EV because the packaging and thermal problems are the same, at higher volume and faster iteration.

Resume attached. Could we speak for 15 minutes this week?

Shan""",
        "revise": "• Sheet-metal DFM: bend radius, K-factor, hole-to-edge rules\n• Sealing and IP testing; thermal design for enclosures\n• Cost-down examples ($0.3/unit, 8x connector)\n• BOM costing and tooling transfer from Chennai setup",
        "learn": "• DFMEA and DVP structure\n• AIS-156 and AIS-038 scope; battery pack basics\n• Vehicle packaging and CATIA or NX basics\n• Fatigue and NVH basics"
    },
    "consumer": {
        "name": "Consumer / Industrial Products",
        "resume": "Shan_resume_consumer.pdf",
        "targets": ["Whirlpool", "Bajaj", "Havells", "Godrej", "Philips", "Cummins", "Caterpillar", "Siemens", "Hitachi Energy", "GE Vernova", "Schneider", "ABB", "Vestas", "Suzlon"],
        "subject": "Mechanical Design Engineer, {company}: DFM, injection molding, tolerance stack-up",
        "note_template": """Hi {name},

Your posting asks for {jd_hook}. I owned NPD and NPI for eight products built from those processes, lifted a fixture's yield from 60% to 95%, lowered radome cost by 8%, and saved $0.3 per unit with a snap-fit redesign that removed two components. I built Excel tools to predict snap-joint behavior and ran non-linear snap-fit FEA.

My gaps are mold-flow simulation and formal VAVE. I want consumer/industrial products because the volumes make design decisions matter in rupees per unit.

Resume attached. Could we speak for 15 minutes?

Shan""",
        "revise": "• Injection molding DFM: draft, wall thickness, ribs, gates, weld lines, sink\n• Die-casting and sheet-metal DFM\n• Snap-fit equations and Excel tool logic\n• Tolerance stack-up worked example\n• Cost estimating: material, cycle time, tooling amortization",
        "learn": "• Mold flow (SolidWorks Plastics or Moldflow)\n• VAVE method\n• Safety standards (IEC 60335) and BIS marking"
    },
    "mechatronics": {
        "name": "Mechatronics",
        "resume": "Shan_resume_mechatronics.pdf",
        "targets": ["Siemens", "Bosch", "ABB", "Havells", "Schneider"],
        "subject": "Mechatronics Engineer, {company}",
        "note_template": """Hi {name},

Your role asks for {jd_hook}. I design electromechanical products that combine RF PCBs, sheet metal and molded parts, developed a pneumatic punching fixture (yield 60% to 95%, two operators to one), and built a 6-DOF robotic arm with real-time mirroring and a 1:64 multi-stage gearbox.

My gap is controls: motor selection, PID tuning and ROS. I am mechanical at heart and want a role where the mechanism, sensing and control are designed together.

Resume attached. Could we talk for 15 minutes?

Shan""",
        "revise": "• Kinematics, gear ratios, torque and speed calculations\n• Encoders, limit sensing and basic sensors\n• PID basics and Simscape modeling\n• 6-DOF arm motion mirroring data path\n• Pneumatic fixture design logic",
        "learn": "• BLDC and servo selection and sizing\n• PID tuning\n• ROS basics & PLC awareness"
    },
    "robotics": {
        "name": "Robotics",
        "resume": "Shan_resume_robotics.pdf",
        "targets": ["Svaya Robotics", "Addverb", "Ati Motors", "Peer Robotics", "CynLr", "Armatrix", "Genrobotics"],
        "subject": "Mechanical Design Engineer, Robotics: {company}",
        "note_template": """Hi {name},

Your posting asks for {jd_hook}. I built a 6-DOF robotic arm with real-time mirroring, a 1:64 multi-stage gearbox and a cam-lever anchor gripper, and at JMA I developed a pneumatic punching fixture that cut a two-person task to one operator and lifted yield from 60% to 95%. My fixtures cut rework 40% and riveting time 75%.

My gap is actuator and gearbox selection (harmonic and planetary drives) and ROS. I want to move into robotics because I enjoy mechanisms and fixtures most, and I have been building robots on my own time.

Resume attached. Could we speak for 15 minutes?

Shan""",
        "revise": "• DOF, joint design, payload and reach calculations\n• Gear types, backlash, bearings, tolerances\n• FDM prototyping, orientation, post-processing\n• Gripper and gearbox design decisions\n• DFMA examples",
        "learn": "• Motor and gearbox sizing, harmonic and planetary drives\n• Actuator selection and robot safety standards\n• ROS basics"
    },
    "automation": {
        "name": "Automation / Machine Design",
        "resume": "Shan_resume_automation.pdf",
        "targets": ["Capgemini", "Atlas Copco", "Siemens", "Ethereal Machines", "Divide By Zero", "Tvasta"],
        "subject": "Machine Design Engineer, {company}: fixtures, pneumatics, SPM",
        "note_template": """Hi {name},

Your posting asks for {jd_hook}. I developed a pneumatic-actuated pivot punching fixture that turned a two-person task into one operator's job and lifted yield from 60% to 95%, saving $0.4 per failed cycle. I sized the cylinder with my own crimp-force calculations, built RF assembly fixtures and press tools that cut rework 40%, and designed a 1:64 gearbox for a conveyor platform.

My gap is full SPM scope: PLC integration, machine safety standards and pneumatic circuit design beyond one cylinder. I want to build machines full time because that is where my best results came from.

Resume attached. Could we speak for 15 minutes?

Shan""",
        "revise": "• Cylinder force calculation & crimp-force logic\n• Fixture principles: 3-2-1 locating, clamping, GD&T\n• Conveyor and gearbox power calculations\n• The yield story: root cause, fix, result",
        "learn": "• Pneumatic circuits: valves, FRL, speed control, symbols\n• Machine safety and guarding basics\n• Motor and conveyor sizing\n• PLC and sensor integration"
    },
    "drones": {
        "name": "Drones / UAV",
        "resume": "Shan_resume_drones.pdf",
        "targets": ["ideaForge", "Unmannd", "Throttle Aerospace", "Aerial IQ", "Marut Drones", "Sarla Aviation", "ePlane"],
        "subject": "Mechanical Design Engineer, UAV: {company}",
        "note_template": """Hi {name},

Your role asks for {jd_hook}. I cut 60 g per unit with topology-optimized 3D-printed parts, ran Ansys Fluent CFD on 135+ radome profiles for 12 to 18% wind load reduction, and designed parametric propeller blades from NACA and Eppler airfoils (GitHub, linked on my resume).

My gaps are propulsion matching, composites and flight testing. I am moving into drones because my strongest skills are lightweight design and aerodynamics, and I want them in a flying product.

Resume attached. Could we talk for 15 minutes?

Shan""",
        "revise": "• Airfoils, Reynolds number, lift and drag\n• Propeller basics: pitch, diameter, tip speed\n• Lightweight design and FDM materials (nylon, carbon-filled)\n• Blade design parameters and CFD setup",
        "learn": "• Motor, propeller and ESC matching; thrust estimation\n• Composite layup basics\n• PX4 or ArduPilot basics\n• DGCA drone rules"
    },
    "semiconductor": {
        "name": "Semiconductor Equipment",
        "resume": "Shan_resume_semiconductor.pdf",
        "targets": ["Applied Materials", "Lam Research", "KLA", "NXP", "Thermo Fisher", "Medtronic", "Stryker", "Analog Devices", "Infineon"],
        "subject": "Mechanical Engineer, {company}: precision electromechanical design",
        "note_template": """Hi {name},

Your posting asks for {jd_hook}. I release CNC, EDM, sheet-metal and molded parts at a 90% FAI pass rate, design precision assembly fixtures that cut rework 40%, and run vibration and thermal analysis for products qualified to IEC 60068.

I have not worked on vacuum or process equipment. I want to move into semiconductor/precision equipment because the precision demands match how I like to work.

Resume attached. Could we speak for 15 minutes?

Shan""",
        "revise": "• GD&T and tolerance stack-up with worked examples\n• Thermal expansion and drift\n• Vibration isolation and stiffness basics\n• Materials (stainless steel, aluminum) and fastening\n• Fixture and FAI stories",
        "learn": "• Vacuum basics and semiconductor process overview\n• Equipment safety standards (SEMI S2)\n• Kinematic couplings, flexures, cleanliness basics"
    }
}