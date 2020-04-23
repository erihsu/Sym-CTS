#!/usr/bin/perl
###############################################################################
# 
# ISPD 2009 Clock Synthesis Contest Evaluation Script
# 
# Copyright (c) Cliff Sze (csze@us.ibm.com)
#
###############################################################################
# 
# Logs:
# 2009/03/29   less memory usage, same results
# 2009/03/28   detect real latency
# 2009/03/27   detect non-tree
# 2009/03/27   add more cap stat
# 2009/03/08   bug fix: wrong .ic definition for SEG_NODE_*
# 2009/03/03   bug fix: wrong sink idenfication, due to order of merge_neighbor_node invocation
# 2009/02/24   bug fix: a very special case causes wrong sink idenfication
# 2009/02/18   added a switch "-b" to ignore blockage violation
# 2009/02/16   bug fix: ".print tran" cannot take more than 71 arguments
# 2009/02/16   bug fix: remove segmented wire resistance
# 2009/02/03   node coordinates don't have to be integer, use \S instead
#              we can also use [-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)? if needed
# 2009/01/31   handles the 15-column reporting of ngspice for 14+ voltage points
# 2009/01/31   added long interconnect segmentation to be < 500um
#              this is to account for the "shielding effect of the interconnect resistance"
# 2009/01/31   added blockage checking 
# 2009/01/30   added checks about source id, sink id, buffer type and wire code
# 2009/01/18   fixed the bug of buffer-added-to-source, when source is (-1, -1)
# 2009/01/10   fixed the bug of blockage reading
# 2009/01/08   first release
# 2009/01/01   Created
#              - Thanks for the help (ngspice/tcl examples) from Zhuo Li, lizhuo@us.ibm.com
# 
# units:
#   voltage  V
#   temp     deg celsius
#   cap      fF


######################################################################
# Add-on:
# extract.pl is mostly from original evaluation script. We remove some code from origin file.
# If you want to use full function of ispd2009 evaluation,please download it from ispd2009 contest website
######################################################################
use Getopt::Std;
use POSIX qw(ceil floor);

###############################################################################
# Process all the switches
# -h help
# -v verbose level
# 
getopts('sSbHhmv:');

$MAX_WIRE_LENGTH=500000; # cut long wire until each segment is shorter than 500um

if($#ARGV != 2 || $opt_h || $opt_H ) {
    print STDERR "Usage: $0 [Options] [input design] [clock result] [model card file]\n";
    print STDERR "Options: -v [level]       Verbosity level (0-2)\n";
    print STDERR "         -s               do not abort if slew violation exists\n";
    print STDERR "         -b               do not abort if placement blockage violation exists\n";
    print STDERR "         -m               check for non-tree (beta)\n";
    print STDERR "         -h               this (help) message\n";
    print STDERR "Notes: C      - Cap estimation (in fF)\n";
    print STDERR "       CLR    - Clock Latency Range\n";
    print STDERR "       Units of Latency and slew are in ps\n";
    exit 0;
}
#############
$inFile = $ARGV[0];
die "ERROR missing input file," unless(-f $inFile);
$resultFile = $ARGV[1];
die "ERROR missing clock result file," unless(-f $resultFile);
$modelCardFile = $ARGV[2];
die "ERROR missing model card file," unless(-f $modelCardFile);

$inFileO = $inFile;
$resultFileO = $resultFile;
$modelCardFileO = $modelCardFile;

if($inFile =~ /\.gz$/) {
    $inFile = "gzip -dc $inFile |";
}
elsif($inFile =~ /\.bz2$/) {
    $inFile = "bzip2 -dc $inFile |";
}
if($resultFile =~ /\.gz$/) {
    $resultFile = "gzip -dc $resultFile |";
}
elsif($resultFile =~ /\.bz2$/) {
    $resultFile = "bzip2 -dc $resultFile |";
}
if($modelCardFile =~ /\.gz$/) {
    $modelCardFile = "gzip -dc $modelCardFile |";
}
elsif($modelCardFile =~ /\.bz2$/) {
    $modelCardFile = "bzip2 -dc $modelCardFile |";
}

###############################################################################
# Process input file
#
open INFILE, "$inFile";
#song: read one line
$_ = <INFILE>;
#song: match the first line 
die "ERROR" unless(/^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$/);
$llx = $1; $lly = $2; $urx = $3; $ury = $4;

#song: match the second line
$ssCount = 0;
$_ = <INFILE>;
die "ERROR" unless(/^\s*source\s+(\S+)\s+(\d+)\s+(\d+)\s+(\S+)\s*$/);
$id = $1; $x = $2; $y = $3; $srcBufId = $4;
die "ERROR: 2 sinks have same sink id in $inFileO," if $ssExistInInputFile{$id}++; #song:the ssExistInInputFile is a hash table. if the value of key id is not zero, there would be same sink id
push @ssIdArr, $id;
push @ssXArr, $x;
push @ssYArr, $y;
push @ssCapArr, -1;
$CountFromSsId{$id} = $ssCount++;

#song: get sink datas
$_ = <INFILE>;
die "ERROR" unless(/^\s*num\s+sink\s+(\d+)\s*$/);
$numSink= $1;
for $i (0 .. ($numSink - 1)) {
  $_ = <INFILE>;
  die "ERROR" unless(/^\s*(\S+)\s+(\d+)\s+(\d+)\s+(\S+)\s*$/);
  $id = $1; $x = $2; $y = $3; $cap = $4; #id can be a string
  die "ERROR: 2 sinks have same sink id in $inFileO," if $ssExistInInputFile{$id}++;
  push @ssIdArr, $id;
  push @ssXArr, $x;
  push @ssYArr, $y;
  push @ssCapArr, $cap;
  $CountFromSsId{$id} = $ssCount++; #song:  id 在列表中的位置
  $sinkUncovered{$id} = 1;
}


#song: get wire lib data
$_ = <INFILE>;
die "ERROR" unless(/^\s*num\s+wirelib\s+(\d+)\s*$/);
$numWireCode = $1;
$wcCount = 0;
for $i (0 .. ($numWireCode - 1)) {
  $_ = <INFILE>;
  die "ERROR" unless(/^\s*(\S+)\s+(\S+)\s+(\S+)\s*$/);
  $id = $1; $unitR = $2; $unitC = $3; #id can be a string
  die "ERROR: 2 wires have same wire id in $inFileO," if $wcExistInInputFile{$id}++;
  push @wcIdArr, $id;
  push @wcRArr, $unitR;
  push @wcCArr, $unitC;
  $CountFromWcId{$id} = $wcCount++;
}

#song: get buf lib data
$_ = <INFILE>;
die "ERROR" unless(/^\s*num\s+buflib\s+(\d+)\s*$/);
$numBufLib = $1;
$bufLibCount = 0;
for $i (0 .. ($numBufLib - 1)) {
  $_ = <INFILE>;
  die "ERROR" unless(/^\s*(\S+)\s+(\S+)\s+(\d+)\s+(\d+\.*\d*)\s+(\d+\.*\d*)\s+(\d+\.*\d*)\s*$/);
  $id = $1; $subckt = $2; $inv = $3; $inCap = $4; $outCap = $5; $outRes = $5; #id can be a string
  die "ERROR fail to read subcircuit file $subckt," unless (-r $subckt);
  die "ERROR: 2 buffers have same buf id in $inFileO," if $bufLibExistInInputFile{$id}++;
  die "ERROR buf $id is neither non-inverted nor inverted," unless inv == 0 or inv == 1;
  push @bufLibIdArr, $id;
  push @bufLibSubcktArr, $subckt;
  push @bufLibIsInvArr, $inv;
  push @bufLibInCArr, $inCap;
  push @bufLibOutCArr, $outCap;
  push @bufLibOutRArr, $outRes;
  $CountFromBufLibId{$id} = $bufLibCount++;
}
die "ERROR: buffer at source ($srcBufId) is not defined," unless $bufLibExistInInputFile{$srcBufId};

#song: get voltage, slew and capacity limit
$_ = <INFILE>;
die "ERROR" unless(/^\s*simulation\s+vdd\s+(.+)\s*$/);
@vArr= split /\s+/, $1;

$_ = <INFILE>;
die "ERROR" unless(/^\s*limit\s+slew\s+(\S+)\s*$/);
$SLEWLIMIT = $1;

$_ = <INFILE>;
die "ERROR" unless(/^\s*limit\s+cap\s+(\S+)\s*$/);
$CAPLIMIT = $1;

$_ = <INFILE>;
die "ERROR" unless(/^\s*num\s+blockage\s+(\d+)\s*$/);
$numBlockage = $1;
for $i (0 .. ($numBlockage - 1)) {
  $_ = <INFILE>;
  die "ERROR" unless(/^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$/);
  push @llxBlockArr, $1;
  push @llyBlockArr, $2;
  push @urxBlockArr, $3;
  push @uryBlockArr, $4;
}

#song: output data
debug_infile();
close INFILE;

###############################################################################
# Process result file
#
$nodeCount = 0;
open RFILE, "$resultFile";

#song: read soure and node data
$_ = <RFILE>;
die "ERROR" unless(/^\s*sourcenode\s+(\S+)\s+(\S+)\s*$/);
$id= $1; $srcId = $2;
die "ERROR: 2 nodes have same node id in $resultFileO," if $nodeExistInResultFile{$id}++;
die "ERROR: sourcenode does not point to source id in $resultFileO," if $srcId ne $ssIdArr[0];
push @nodeIdArr, $id;
push @nodeSsIdArr, $srcId;
push @nodeXArr, -1; push @nodeYArr, -1; push @nodeMergedTo, "__none__"; push @totCap, 0; push @isInv, -1;
$CountFromNodeId{$id} = $nodeCount++;

$_ = <RFILE>;
die "ERROR" unless(/^\s*num\s+node\s+(\d+)\s*$/);
$numNode= $1;
for $i (0 .. ($numNode - 1)) {
  $_ = <RFILE>;
  die "ERROR" unless(/^\s*(\S+)\s+(\S+)\s+(\S+)\s*$/);
  $id = $1; $x = $2; $y = $3; #id can be a string
  die "ERROR: 2 nodes have same node id in $resultFileO," if $nodeExistInResultFile{$id}++;
  push @nodeIdArr, $id;
  push @nodeSsIdArr, "__internal__";
  push @nodeXArr, $x; push @nodeYArr, $y; push @nodeMergedTo, "__none__"; push @totCap, 0; push @isInv, -1;
  $CountFromNodeId{$id} = $nodeCount++;
}

$_ = <RFILE>;
die "ERROR" unless(/^\s*num\s+sinknode\s+(\d+)\s*$/);
$numSinkNode= $1;
$sinkNodeCount = 0;
for $i (0 .. ($numSinkNode - 1)) {
  $_ = <RFILE>;
  die "ERROR" unless(/^\s*(\S+)\s+(\S+)\s*$/);
  $id = $1; $sinkId = $2; #id can be a string
  die "ERROR: 2 nodes have same node id in $resultFileO," if $nodeExistInResultFile{$id}++;     #song: 检查是否重复 
  die "ERROR: sink id ($sinkId) not defined in $inFileO," unless $ssExistInInputFile{$sinkId};  #song: 检查是否在输入文件出现过，如果出现过hash表表项的值为1
  push @nodeIdArr, $id;
  push @nodeSsIdArr, $sinkId;
  push @nodeXArr, -1; push @nodeYArr, -1; push @nodeMergedTo, "__none__"; push @totCap, 0; push @isInv, -1;
  $CountFromNodeId{$id} = $nodeCount++;
  delete $sinkUncovered{$sinkId};
  $sinkUncoveredByResult{$id} = 1;
}

die "ERROR clock net does not cover all sinks," if (keys %sinkUncovered);   #song:  检查输入网表寄存器是否全在网表里
# update x and y of source and sink
# song: 更新位置信息
for $i (0 .. ($#nodeIdArr )) {
    if ($nodeSsIdArr[$i] eq $ssIdArr[0]) { 
        $nodeXArr[$i] = $ssXArr[$CountFromSsId{$nodeSsIdArr[$i]}];
        $nodeYArr[$i] = $ssYArr[$CountFromSsId{$nodeSsIdArr[$i]}];
    } elsif ($nodeSsIdArr[$i] ne "__internal__" ) { 
        $nodeXArr[$i] = $ssXArr[$CountFromSsId{$nodeSsIdArr[$i]}];
        $nodeYArr[$i] = $ssYArr[$CountFromSsId{$nodeSsIdArr[$i]}];
    }
}

$_ = <RFILE>;
die "ERROR" unless(/^\s*num\s+wire\s+(\d+)\s*$/);
$numWire = $1;
for $i (0 .. ($numWire - 1)) {
  $_ = <RFILE>;
  die "ERROR" unless(/^\s*(\S+)\s+(\S+)\s+(\S+)\s*$/);
  $from = $1; $to = $2; $wc = $3;
  die "ERROR: wire code ($wc) not defined in $inFileO," unless $wcExistInInputFile{$wc};
  push @wireFromArr, $from;
  push @wireToArr, $to;
  push @wireWcArr, $wc;
  die "ERROR wire connects two nodes with same id," if ( $from eq $to );
}

$_ = <RFILE>;
die "ERROR" unless(/^\s*num\s+buffer\s+(\d+)\s*$/);
$numBuffer = $1;
for $i (0 .. ($numBuffer - 1)) {
  $_ = <RFILE>;
  die "ERROR" unless(/^\s*(\S+)\s+(\S+)\s+(\S+)\s*$/);
  $from = $1; $to = $2; $bufId= $3;
  die "ERROR: buffer type ($bufId) not defined in $inFileO," unless $bufLibExistInInputFile{$bufId};
  die "ERROR buffer connects two nodes with same id," if ( $from eq $to );
  die "ERROR buffer connects two nodes at distinct coordinates," if ( $nodeXArr[$CountFromNodeId{$from}] != $nodeXArr[$CountFromNodeId{$to}] || $nodeYArr[$CountFromNodeId{$from}] != $nodeYArr[$CountFromNodeId{$to}] );
  if ( $opt_b ){
    print "ERROR: buffer ($from->$to) overlaps blockage.\n" if check_blockage_overlap($nodeXArr[$CountFromNodeId{$from}], $nodeYArr[$CountFromNodeId{$from}]);
  } else {
    die "ERROR: buffer ($from->$to) overlaps blockage," if check_blockage_overlap($nodeXArr[$CountFromNodeId{$from}], $nodeYArr[$CountFromNodeId{$from}]);
  }
  push @bufFromArr, $from;
  push @bufToArr, $to;
  push @bufBufIdArr, $bufId;
}

close RFILE;

###############################################################################
# Construct a 2-D array showing connections
#
push @neighbor, ();
push @bufNeighbor, ();
push @invNeighbor, ();
#song:  两重循环
#song:  建立邻接表
for $i (0 .. ($#nodeIdArr )) {
    push @{$neighbor[$i]}, ();
    for $j (0 .. ($#wireFromArr )) {
        push @{$neighbor[$i]}, $wireToArr[$j] if ( $wireFromArr[$j] eq $nodeIdArr[$i] );
        push @{$neighbor[$i]}, $wireFromArr[$j] if ( $wireToArr[$j] eq $nodeIdArr[$i] );
    }
    for $j (0 .. ($#bufFromArr )) {
        if ( $bufLibIsInvArr[$CountFromBufLibId{$bufBufIdArr[$j]}] == 0 ){
            push @{$bufNeighbor[$i]}, $bufToArr[$j] if ( $bufFromArr[$j] eq $nodeIdArr[$i] );
            push @{$bufNeighbor[$i]}, $bufFromArr[$j] if ( $bufToArr[$j] eq $nodeIdArr[$i] );
        } else {
            push @{$invNeighbor[$i]}, $bufToArr[$j] if ( $bufFromArr[$j] eq $nodeIdArr[$i] );
            push @{$invNeighbor[$i]}, $bufFromArr[$j] if ( $bufToArr[$j] eq $nodeIdArr[$i] );
        }
    }
}

###############################################################################
# Check results
# 1. all nodes are connected to source?
# 2. all sinks are non-inverted?
# Other tasks
# 1. collect the polarity of all node (for .ic)
# 2. collect all the input of buffers (for .print tran)
###############################################################################
# NOTE: do it before merge_neighbor_node
# NOTE: do it after constructing @neighbor and @bufNeighbor
#
for $i (0 .. ($#nodeIdArr )) {
    if ($nodeSsIdArr[$i] eq $ssIdArr[0]) { 
        $thisIsInv = 1; # sourcenode is "inverted"
        check_node_is_inverted($i,$thisIsInv);
        if ( $opt_m > 0 ){ 
            $NONTREE = 0;
            check_non_tree(-1,$i,0);
        }
    }
}
for $i (0 .. ($#nodeIdArr )) {
    die "ERROR node $nodeIdArr[$i] is not connect to the clock network," if $isInv[$i] == -1;
    if ($nodeSsIdArr[$i] ne $ssIdArr[0] && $nodeSsIdArr[$i] ne "__internal__" ) { 
      #  die "ERROR sinknode $nodeIdArr[$i] is inverted," if $isInv[$i] == 1;
    }
}

###############################################################################
# Merge "zero-distance" pair of nodes
# This step is to make sure there is no "0 ohm" wire in the SPICE file, which
# is a necessary condition for SPICE simulation. 
# Based on the same reason, no sink can be at the same location as the source
#
push @nodeMergedTo, ();
# merge-to source/sink first (assume no sink is at exact same location as the source)
# It is to make sure source/sink won't merge to internal nodes
for $i (0 .. ($#nodeIdArr )) {
    next if ($nodeSsIdArr[$i] eq "__internal__" );
    next if $nodeMergedTo[$i] ne "__none__";
    merge_neighbor_node($i,"no_orig");
}
# merge internal nodes later
for $i (0 .. ($#nodeIdArr )) {
    if ($nodeSsIdArr[$i] eq "__internal__" ) { 
        next if $nodeMergedTo[$i] ne "__none__";
        merge_neighbor_node($i,"no_orig");
    }
}
debug_resultfile();
debug_neighbor();

###############################################################################
# segmentation of long interconnect, create extra nodes
#
#song:  分割长连线
#song:  遍历连线数组
for $j (0 .. ($#wireFromArr )) {
    last if ( $opt_S );
    $from = $wireFromArr[$j];
    $to = $wireToArr[$j];
    $wc = $wireWcArr[$j];
    $countFrom = $CountFromNodeId{$from};
    $countTo = $CountFromNodeId{$to};
    #song:  如果长度为零就跳出本次循环
    next if ( $nodeXArr[$countFrom] == $nodeXArr[$countTo] && $nodeYArr[$countFrom] == $nodeYArr[$countTo] );
    $xDist = abs($nodeXArr[$countFrom] - $nodeXArr[$countTo]);
    $yDist = abs($nodeYArr[$countFrom] - $nodeYArr[$countTo]);
    #song:  不是长连线的话就跳出本次循环
    next if ($xDist + $yDist) <= $MAX_WIRE_LENGTH;
    #song:  分多少段
    $numSeg = ceil( ($xDist + $yDist)/ $MAX_WIRE_LENGTH );
    $xSegLen = ceil( $xDist / $numSeg );
    $ySegLen = ceil( $yDist / $numSeg );
    #DEBUG# print "($nodeXArr[$countFrom],$nodeYArr[$countFrom])->($nodeXArr[$countTo],$nodeYArr[$countTo])\n";
    #DEBUG# print "wc $wc xDist $xDist yDist $yDist MAX_WIRE_LENGTH $MAX_WIRE_LENGTH numSeg $numSeg xSegLen $xSegLen ySegLen $ySegLen\n";
    $xInc = 1; $yInc = 1;
    $xInc = -1 if $nodeXArr[$countFrom] > $nodeXArr[$countTo];
    $yInc = -1 if $nodeYArr[$countFrom] > $nodeYArr[$countTo];
    $xInc = 0 if $xDist < 1;
    $yInc = 0 if $yDist < 1;
    $newX = $nodeXArr[$countFrom]; $newY = $nodeYArr[$countFrom];
    $wireWcArr[$j] = "__segmented__";   #song:  标示为被划分的线
    die "ERROR script internal bug," if $isInv[$countTo] != $isInv[$countFrom];
    $segIsInv = $isInv[$countFrom];
    ########
    # add new nodes between "from" and "to"
    for $segCnt (1 .. $numSeg-1) {
        $newX += $xInc * $xSegLen; $newY += $yInc * $ySegLen; 
        $id = "SEG_NODE_".$nodeCount;
        #DEBUG# print "id $id newX $newX newY $newY inv $segIsInv\n"; 
        push @nodeIdArr, $id;
        push @nodeSsIdArr, "__internal__";
        push @nodeXArr, $newX; push @nodeYArr, $newY; push @nodeMergedTo, "__none__"; push @totCap, 0; push @isInv, $segIsInv;
        $CountFromNodeId{$id} = $nodeCount++;
        push @wireFromArr, $from;
        push @wireToArr, $id;
        push @wireWcArr, $wc;
        $from = $id;
    }
    push @wireFromArr, $from;
    push @wireToArr, $to;
    push @wireWcArr, $wc;
}

#song： 提取寄生参数
###############################################################################
# Calculate distributed R and C
#
$resultTotCap=0;
for $j (0 .. ($#wireFromArr )) {
    $from = $wireFromArr[$j];
    $to = $wireToArr[$j];
    $countFrom = $CountFromNodeId{$from};
    $countTo = $CountFromNodeId{$to};
    next if $wireWcArr[$j] eq "__segmented__";
    next if ( $nodeXArr[$countFrom] == $nodeXArr[$countTo] && $nodeYArr[$countFrom] == $nodeYArr[$countTo] );
    $mDist = abs($nodeXArr[$countFrom] - $nodeXArr[$countTo]) + abs($nodeYArr[$countFrom] - $nodeYArr[$countTo]);
    #DEBUG# print "$mDist = $nodeXArr[$countFrom] - $nodeXArr[$countTo] + $nodeYArr[$countFrom] - $nodeYArr[$countTo] ( $countFrom $countTo ) \n";
    $fullRes = $mDist * $wcRArr[$CountFromWcId{$wireWcArr[$j]}];
    $halfCap = 0.5 * $mDist * $wcCArr[$CountFromWcId{$wireWcArr[$j]}];
    $from = $nodeMergedTo[$CountFromNodeId{$from}] if $nodeMergedTo[$CountFromNodeId{$from}] ne "__none__";
    $to = $nodeMergedTo[$CountFromNodeId{$to}] if $nodeMergedTo[$CountFromNodeId{$to}] ne "__none__";
    $totCap[$CountFromNodeId{$from}] += $halfCap;
    $totCap[$CountFromNodeId{$to}] += $halfCap;
    #DEBUG# print "cap $CountFromNodeId{$from} + $halfCap \n";
    #DEBUG# print "res $CountFromNodeId{$from} $CountFromNodeId{$to}  + $fullRes \n";
    $resultTotCap += 2.0 * $halfCap;
}
$totWireCap = $resultTotCap;
#### sum up cap of mergedTo nodes
for $i (0 .. ($#nodeIdArr )) {
    if ($nodeSsIdArr[$i] ne $ssIdArr[0] && $nodeSsIdArr[$i] ne "__internal__" ) { 
        $sinkCap = $ssCapArr[$CountFromSsId{$nodeSsIdArr[$i]}];
        $j = $i;
        $j = $nodeMergedTo[$i] if $nodeMergedTo[$i] ne "__none__";
        $totCap[$j] += $sinkCap;
        $resultTotCap += $sinkCap;
    }
}
$totSinkCap = $resultTotCap - $totWireCap;

$resultTotCap += $bufLibInCArr[$CountFromBufLibId{$srcBufId}];
$resultTotCap += $bufLibOutCArr[$CountFromBufLibId{$srcBufId}];
for $j (0 .. ($#bufFromArr )) {
    $resultTotCap += $bufLibInCArr[$CountFromBufLibId{$bufBufIdArr[$j]}];
    $resultTotCap += $bufLibOutCArr[$CountFromBufLibId{$bufBufIdArr[$j]}];
}
$totBufCap = $resultTotCap - $totWireCap - $totSinkCap;

###############################################################################
###############################################################################
#
#  START SIMULATION
#
###############################################################################
###############################################################################

@srcTrans4Test = ( "1" ); # 0 = rising, 1 = falling
# @srcTrans4Test = ( "0", "1" ); # 0 = rising, 1 = falling
$firstTime = 1;
$minLatency = 100000;
$maxLatency = 0;
$maxNominalSkew = 0;

foreach $vdd (@vArr){
    printf ("=== vdd %.1f\n", $vdd) if ( $opt_v > 0 );
    foreach $srcTrans (@srcTrans4Test){
        if ( $opt_v > 0 ){ 
            printf ("  === clk src rising\n", $vdd) if $srcTrans == 0;
            printf ("  === clk src falling\n", $vdd) if $srcTrans == 1;
        }
$sourceInitVolt = $srcTrans * $vdd;
$sourceEndVolt = (1-$srcTrans)*$vdd;

###############################################################################
# Write spice files
#
#song:  写出spice文件
open OUTFILE, "> $resultFile\.spice";
for $i (0 .. ($#bufLibIdArr )) {
    open SUBCKTFILE, "$bufLibSubcktArr[$i]" or die $!;
    while (<SUBCKTFILE>){
        print OUTFILE;
        if (/\.subckt /){
            @subcktTitle = split;
            push @bufLibSubcktNameArr, $subcktTitle[1] if $firstTime;
        }
    }
    close SUBCKTFILE;
}
#song:  写出电容部分
$capCount=$resCount=$bufCount=0;
for $i (0 .. ($#nodeIdArr )) {
    next if $nodeMergedTo[$i] ne "__none__";
    print OUTFILE "c$capCount n$nodeIdArr[$i] 0 $totCap[$i]f\n";
    $capCount++;
}
#song:  写出电阻部分
for $j (0 .. ($#wireFromArr )) {
    next if $wireWcArr[$j] eq "__segmented__";
    $from = $wireFromArr[$j];
    $to = $wireToArr[$j];
    $countFrom = $CountFromNodeId{$from};
    $countTo = $CountFromNodeId{$to};
    next if ( $nodeXArr[$countFrom] == $nodeXArr[$countTo] && $nodeYArr[$countFrom] == $nodeYArr[$countTo] );
    $mDist = abs($nodeXArr[$countFrom] - $nodeXArr[$countTo]) + abs($nodeYArr[$countFrom] - $nodeYArr[$countTo]);
    $fullRes = $mDist * $wcRArr[$CountFromWcId{$wireWcArr[$j]}];
    $from = $nodeMergedTo[$CountFromNodeId{$from}] if $nodeMergedTo[$CountFromNodeId{$from}] ne "__none__";
    $to = $nodeMergedTo[$CountFromNodeId{$to}] if $nodeMergedTo[$CountFromNodeId{$to}] ne "__none__";
    print OUTFILE "r$resCount n$from n$to $fullRes\n";
    $resCount++;
}
#song:  写出buf部分
for $i (0 .. ($#nodeIdArr )) {
    if ($nodeSsIdArr[$i] eq $ssIdArr[0]) { 
        $i = $nodeMergedTo[$i] if $nodeMergedTo[$i] ne "__none__";
        print OUTFILE "x$bufCount gin n$nodeIdArr[$i] vdd $bufLibSubcktNameArr[$CountFromBufLibId{$srcBufId}]\n";
        last;
    }
}
for $i (0 .. ($#bufFromArr )) {
    $bufCount++;
    $from = $bufFromArr[$i];
    $to = $bufToArr[$i];
    $countFrom = $CountFromNodeId{$from};
    $countTo = $CountFromNodeId{$to};
    $from = $nodeMergedTo[$CountFromNodeId{$from}] if $nodeMergedTo[$CountFromNodeId{$from}] ne "__none__";
    $to = $nodeMergedTo[$CountFromNodeId{$to}] if $nodeMergedTo[$CountFromNodeId{$to}] ne "__none__";
    #DEBUG# print "buf $bufFromArr[$i] $bufToArr[$i] vdd $bufLibSubcktNameArr[$CountFromBufLibId{$bufBufIdArr[$i]}]\n";
    print OUTFILE "x$bufCount n$from n$to vdd $bufLibSubcktNameArr[$CountFromBufLibId{$bufBufIdArr[$i]}]\n";
    push @monitorTheseNodes, "$from" unless $addedToMonitorTheseNodes{$from}++ or $firstTime == 0;
}
foreach $id (@monitorTheseNodes){
    $id =~ tr/A-Z/a-z/;
    $nodeIsBeingMonitored{$id}++;
}
for $i (0 .. ($#nodeIdArr )) {
    if ($nodeSsIdArr[$i] ne $ssIdArr[0] && $nodeSsIdArr[$i] ne "__internal__" ) { 
        $j = $i;
        $j = $nodeMergedTo[$i] if $nodeMergedTo[$i] ne "__none__";
        if ( $firstTime ) {
            push @monitorTheseNodes, "$nodeIdArr[$j]";
            $id = $nodeIdArr[$j];
            $id =~ tr/A-Z/a-z/;
            $sinkIsBeingMonitored{$id}++;
            $numSinkInMonitor++;
        }
    }
}
close OUTFILE;
$firstTime = 0;
} # END of foreach $srcTrans (@srcTrans4Test)
} # END of foreach $vdd (@vArr)
###############################################################################
###############################################################################
# SUBROUTINE
###############################################################################
###############################################################################

sub debug_infile {
    return if ( $opt_v < 2 );
    print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n";
    print "^^^^^^       DUMP INPUT FILE               ^^^^^^^^\n";
    print "source $ssIdArr[0] $ssXArr[0] $ssYArr[0] $ssCapArr[0]\n";
    for $i (1 .. ($#ssIdArr )) {
        print "sink $ssIdArr[$i] $ssXArr[$i] $ssYArr[$i] $ssCapArr[$i]\n";
    }
    for $i (0 .. ($#wcIdArr )) {
        print "wc $wcIdArr[$i] $wcRArr[$i] $wcCArr[$i]\n";
    }
    for $i (0 .. ($#bufLibIdArr )) {
        print "buf $bufLibIdArr[$i] $bufLibSubcktArr[$i] $bufLibInCArr[$i] $bufLibOutCArr[$i]\n";
    }
    for $i (0 .. ($#vArr )) {
        print "voltage $vArr[$i]\n";
    }
    print "slew limit $SLEWLIMIT\n";
    print "cap limit $CAPLIMIT\n";
    print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n";
}

sub debug_resultfile {
    return if ( $opt_v < 2 );
    print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n";
    print "^^^^^^       DUMP RESULT FILE              ^^^^^^^^\n";
    for $i (0 .. ($#nodeIdArr )) {
        if ($nodeSsIdArr[$i] eq $ssIdArr[0]) { 
            print "source $nodeSsIdArr[$i] $nodeIdArr[$i] $nodeXArr[$i] $nodeYArr[$i] $nodeMergedTo[$i]\n"; 
        } elsif ($nodeSsIdArr[$i] eq "__internal__" ) { 
            print "node $nodeIdArr[$i] $nodeXArr[$i] $nodeYArr[$i] $nodeMergedTo[$i]\n"; 
        } else { 
            print "sink $nodeSsIdArr[$i] $nodeIdArr[$i] $nodeXArr[$i] $nodeYArr[$i] $nodeMergedTo[$i]\n"; 
        }
    }
    for $i (0 .. ($#wireFromArr )) {
        print "wire $wireFromArr[$i] $wireToArr[$i] $wireWcArr[$i]\n";
    }
    for $i (0 .. ($#bufFromArr )) {
        print "buf $bufFromArr[$i] $bufToArr[$i] $bufBufIdArr[$i]\n";
    }
    print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n";
}

sub debug_neighbor{
    return if ( $opt_v < 2 );
    print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n";
    print "^^^^^^       DUMP NEIGHBOR                 ^^^^^^^^\n";
    for $i (0 .. ($#nodeIdArr )) {
        print "[$i] neig of $nodeIdArr[$i]: (wire";
        foreach $neig (@{$neighbor[$i]}){
            print " $neig";
        }
        print ") (buf";
        foreach $neig (@{$bufNeighbor[$i]}){
            print " $neig";
        }
        print ") (inv";
        foreach $neig (@{$invNeighbor[$i]}){
            print " $neig";
        }
        print ")\n";
    }
    print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n";
}

sub merge_neighbor_node{
    my $i = shift;
    my $orig = shift;
    foreach $neig (@{$neighbor[$i]}){
        $count = $CountFromNodeId{$neig};
        next if $nodeIdArr[$count] eq $orig;
        next if $nodeMergedTo[$count] ne "__none__";
        if ( $nodeXArr[$count] == $nodeXArr[$i] && $nodeYArr[$count] == $nodeYArr[$i] ){
            if ( $orig eq "no_orig" ) {
                $nodeMergedTo[$count] = $nodeIdArr[$i];
                $orig = $nodeIdArr[$i];
            } else {
                $nodeMergedTo[$count] = $orig;
            }
            merge_neighbor_node($count,$orig);
        }
    }
}
#song: 一些规则性的检查
sub check_node_is_inverted{
    my $i = shift;
    my $thisIsInv = shift;
    #DEBUG# print "INV $nodeIdArr[$i] $thisIsInv\n";
    foreach $neig (@{$neighbor[$i]}){
        $count = $CountFromNodeId{$neig};
        if ( $isInv[$count] == -1 ){
            $isInv[$count] = $thisIsInv;
            check_node_is_inverted($count,$thisIsInv);
        } elsif ( $isInv[$count] != $thisIsInv ){
          die "ERROR node $neig has conflict polarities,";
        }
    }
    foreach $neig (@{$bufNeighbor[$i]}){
        $count = $CountFromNodeId{$neig};
        if ( $isInv[$count] == -1 ){
            $isInv[$count] = $thisIsInv;
            check_node_is_inverted($count,$thisIsInv);
        } elsif ( $isInv[$count] != $thisIsInv ){
          die "ERROR node $neig has conflict polarities,";
        }
    }
    $thisIsInv = 1 - $thisIsInv;
    foreach $neig (@{$invNeighbor[$i]}){
        $count = $CountFromNodeId{$neig};
        if ( $isInv[$count] == -1 ){
            $isInv[$count] = $thisIsInv;
            check_node_is_inverted($count,$thisIsInv);
        } elsif ( $isInv[$count] != $thisIsInv ){
          die "ERROR node $neig has conflict polarities,";
        }
    }
}

sub check_non_tree{
    my $parent = shift;
    my $i = shift;
    my $level = shift;
    return if $NONTREE;
    #DEBUG# print "level of $nodeIdArr[$i] $level\n";
    $NONTREE = 1 if $level[$i];
    if ( $level[$i] ) {
        print "NONTREE trace: $i and $parent is connected\n";
        while ($i) {
            print "$i ($level[$i]) ";
            $i = $parent[$i];
        }
        print "\n";
        $i = $parent;
        while ($i) {
            print "$i ($level[$i]) ";
            $i = $parent[$i];
        }
        print "\n";
        return;
    }
    $level[$i] = $level;
    $parent[$i] = $parent;
    foreach $neig (@{$neighbor[$i]}){
        $count = $CountFromNodeId{$neig};
        next if $count == $parent;
        check_non_tree($i,$count,$level+1);
    }
    foreach $neig (@{$bufNeighbor[$i]}){
        $count = $CountFromNodeId{$neig};
        next if $count == $parent;
        check_non_tree($i,$count,$level+1);
    }
    foreach $neig (@{$invNeighbor[$i]}){
        $count = $CountFromNodeId{$neig};
        next if $count == $parent;
        check_non_tree($i,$count,$level+1);
    }
}

sub check_blockage_overlap{
    my $x = shift;
    my $y = shift;
    for my $i (0 .. ($#llyBlockArr)) {
        if ( $x >= $llxBlockArr[$i] and $x <= $urxBlockArr[$i] and $y >= $llyBlockArr[$i] and $y <= $uryBlockArr[$i] ){
            print "ERROR: buffer at ($x,$y) overlaps blockage ($llxBlockArr[$i], $llyBlockArr[$i], $urxBlockArr[$i], $uryBlockArr[$i])\n";
            return 1;
        }
    }
    return 0;
}

###############################################################################
###############################################################################
# NOTE
###############################################################################
###############################################################################
# List of Errors checking
# CHECK1. buffer from-node and to-node are not at the same x,y
# CHECK2. buffer placed on blockages
# CHECK3. sinks are connected to the source
# CHECK4. all nodes are connected to the net
# CHECK5. all nodes are connected to the source
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
###############################################################################
