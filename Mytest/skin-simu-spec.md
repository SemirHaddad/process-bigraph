# Skin Simulation Specification

## Goal
The goal is to simulate skin aging from the extracellular matrix point of view.
We are simulating the effect of aging on the Dermis, and its extracellular matrix.

The thesis for this simulation is that we are going to ignore cellular senescence, and see what extracellular aging alon can do

## Theory
Skins is made of three layers:
- epidermis - the upper layer with epidermis stem cells that continuously rejunevate the skin interface with the world, made of dead cells
- dermis the intermediate layer made of connective tissues that act as a support for the epidermis. The dermis has two layers
  - The Papillary dermis: The thin, upper layer made of loose connective tissue that interlocks with the epidermis through finger-like projections (dermal papillae). 
  It houses tiny blood vessels and touch receptors.  
  - Reticular dermis: The thick, deeper layer made of dense, net-like connective tissue packed with thick collagen and elastic fibers. 
  It gives skin its strength, structure, and elasticity. It’s thick, and it contains blood vessels, glands, hair follicles, lymphatics, nerves and fat cell.
- The hypodermis, also called subcutaneous tissue or superficial fascia, is the innermost, deepest layer of your skin. 
It sits directly beneath the dermis and attaches your skin to the underlying muscles and bones. It is made of collagen, elastin and lots of adipocytes (fat cells).
It also has large blood vessels and nerves. Its role is as anchoring of the skin, and thanks to fat cells, also energy storage, shock absorption and insulation.

For this simulation we focus on the dermis and ignore the effects on the other layers. 
We take into account only glycation and UV & oxidation:

| Driver	       | Main mechanism	    |Effect|
|---------------|--------------------|--|
| Sugar + time	 | Glycation → AGEs	  |pathological cross-linking|
| UV / ROS	     | ROS → AP-1 → MMPs	 |collagen fragmentation + reduced synthesis|


## Model
The model is:

long-lived collagen  
      ↓  
glycation → non-enzymatic cross-linking   
oxidation / UV → AP-1 signaling → MMP Production → collagen cut in fragment   
↓   
matrix stiffness + architecture change  
↓  
fibroblast mechanosensing changes  
↓  
↓ collagen synthesis  
↑ MMP activity  
↓  
more ECM deterioration  
↓  
inflammation / senescence / stem-cell dysfunction  

## Simulatiom Model

Maybe three processes
```
Composite:
matrix stiffness + architecture integrity 
        IntactCollagen %
        FragmentedCollagen %
        CrosslinkedCollagen %

state = {
    "IntactCollagen": 1.0,
    "FragmentedCollagen": 0.0
    "CrosslinkedCollagen": 0.0
    
    "HealthyFibroblasts": 100,
    "SenescentFibroblasts": 0,

    "MMP1": 0.0,
    "IGF1": 1.0,
}

    
Process 1:
collagen with Glycation and UV & Oxidation as input
⇒ stiffness and architecture integrity


Process 2:
fibroblast activity
- sensible to stiffness and architecture integrity
    FibroblastMechanicalTension (value between 0 and 1)
⇒ collagen synthesis and destruction
    CollagenSynthesisRate
    MMPActivity

Process 3: 
fibroblast scenescence
    -> IGF1 decrease
    -> MMP Increase
```
