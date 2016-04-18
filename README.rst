============
Nitty Griddy
============

Nitty griddy aims to make the deployment of analysis using the Aliroot framework easier and transparent. The goal is to eliminate the ungodly practice of copy-pasting together `run.C` files. A nitty griddy project requires only minimum information, is reproducible and runs seamlessly in `local`, `proof lite` or `grid` mode. It makes it easy to select the datasets as well and suports downloading partial datasets for local offline development. Furthermore, nitty griddy allows for monitoring and interaction with the current status of your grid jobs (eg. executing merges).


Setting up a project
====================

A project lives in its own folder. In this folder, the following files are necessary

configureWagon.C
----------------
The only `.C` file needed. It reflects setting up the options for your task analog to what is done in the lego trains. The shortest possible version, would look something like this: ::

  void configureWagons() {
    gROOT->LoadMacro("$ALICE_PHYSICS/PWGCF/Correlations/macros/c2/AddTaskC2.C");
    AliAnalysisTaskC2* task =
    reinterpret_cast< AliAnalysisTaskC2* > (gROOT->ProcessLine("AddTaskC2()"));
    /*
      Set your options here, similar to what is done in the lego trains
    */
  }


nittygriddy.json
----------------
This file contains some default options as well as depedencies which need to be loaded for execution. Again, this is analogus to the lego train interface. An example file might look like: ::

  [
    {
	"Dependencies":"libOADB.so libSTEERBase.so libAOD.so libANALYSISalice.so libPWGCFCorrelationsC2.so"
    }
  ];


datasets.json
-------------
This file contains information about custom datasets. If the standard ones are used this is not necessary.


Using Nittygriddy
=================

List all dataset::

  $ nitty datasets -l

Show details about dataset::

  $ nitty datasets show LHC10h

Download 5GB of data from the given dataset for offline developing::

  $ nitty datasets download LHC10h_AOD160 --amount=5

Run your analysis in proof lite locally::

  $ nitty run lite LHC10H_AOD160

Or do things with it on the grid::
    
  $ nitty run grid test LHC10H_AOD160
  $ nitty run grid launch LHC10H_AOD160
  $ nitty run grid merge online LHC10H_AOD160 --run=139438
  $ nitty run grid merge offline LHC10H_AOD160


What is happening behind the scene?
===================================

When running your analysis nitty griddy create a new folder in your project folder named after the dataset. It then generates a `run.C` file from your options and copies it into that folder. This `run.C` can be run on independently, if you chose to do so, but it is not recommended to edit it, since it might get overwritten easily.
