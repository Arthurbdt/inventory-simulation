# Inventory simulation

## Description
This repository contains a discrete-event simulation (DES) model of a single product inventory system. It is built on the inventory system described in Law and Kelton's *Simulation Modeling and Analysis (3rd Edition, 2000)*. It is aimed to be used as a tutorial on creating DES models in Python and peforming and statistical analysis of a terminating simulation output.

The model simulates various inventory policy systems and allows users to determine the reorder point and order size parameters minimizing total inventory costs.

## Usage
Import the simulation model:
```
import model
```

## Further work
 - Add additional decision variables to the model (such as frequency of inventory review)
 - Add brief introduction to design of experiments (DOE) like 2k factorial design to illustrate computation and interpretation of main effects and interactions
