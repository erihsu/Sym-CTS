# Sym-CTS

## Introduction  
Sym-CTS is my graduate design which aims to design a symmetric clock tree for Near Threshold-Voltage(NTV) or Ultra-low voltage(ULV) Integrated Circuits Design. Circuits working at NTV suffers great variation and the performance of clock tree can be greatly reduced because of timing variation on clock buffers and clock gates. And symmetric clock tree synthesis(CTS) is a effective way to achieve a robost clock tree design under NTV or ULV.  

The project is currently based on Python3.7.
Warning: The repository is prepared to migrate to Rust version.

## Sym-CTS Flow Outline
1.  Partition
2.  Construction
3.  Buffering
4.  Buffer sizing

## Programming Principles
1. Object Oriented Programming
2. Configurable
3. Reusable


## How To Use
### Prepare Tools
* **python3 & 3rd-party packages**: numpy, pandas, scipy  

* **gnuplot**

* **Hspice-2016**

### Flow it
The given Makefile is only an example of ```usb_phy``` circuits. Before ```make```,make sure ```SYMCTS``` environment variable in the current user. Export ```SYMCTS``` in your shell.


```
export SYMCTS=/path/to/Sym-CTS
```

After ```make```, the folder **workspace** will be created. The synthesized result, input circuit, buffer spice file and mosfet parameter card will be copied to the folder for evaluation.  

To extract rc from synthesized result, just run 

```
perl extract.pl ispd2009f11 result 45_LP.pm
``` 

To show the graphical result, just run 
 
```
perl view.pl result ispd2009f11 
```

To get the statistical results(skew, slew) of clock tree, just run

```
python3 evaluation.py
```


> the extract.pl and view.pl is provided by ispd2009 contest


## Reference
[[1]Shih, Xin-Wei, and Yao-Wen Chang. "Fast timing-model independent buffered clock-tree synthesis." IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems31.9 (2012): 1393-1404.](https://drive.google.com/drive/folders/1pdr5MFKZhDVeKK29NIKPZrMjhalHT_YD)  

[[2]Wang, Chun-Kai, et al. "Clock tree synthesis considering slew effect on supply voltage variation." ACM Transactions on Design Automation of Electronic Systems (TODAES) 20.1 (2014): 3.](https://drive.google.com/drive/folders/1pdr5MFKZhDVeKK29NIKPZrMjhalHT_YD)

[[3]http://www.ispd.cc/contests/09/ispd09cts.html](http://www.ispd.cc/contests/09/ispd09cts.html)
