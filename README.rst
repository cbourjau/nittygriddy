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


nittygriddy.json *(Not used, yet)*
----------------------------------
This file contains some default options as well as depedencies which need to be loaded for execution. Again, this is analogus to the lego train interface. An example file might look like: ::

  [
    {
	"Dependencies":"libOADB.so libSTEERBase.so libAOD.so libANALYSISalice.so libPWGCFCorrelationsC2.so"
    }
  ];


datasets.json *(Not implemented, yet)*
--------------------------------------
This file contains information about custom datasets. If the standard ones are used this is not necessary.


Using Nittygriddy
=================

List all dataset::

  $ nitty datasets -l

Show details about dataset::

  $ nitty datasets --show LHC10h_AOD160

Download 5GB of data from the given dataset for offline developing::

  $ nitty datasets --download LHC10h_AOD160 --volume=5

Run your analysis in proof lite locally::

  $ nitty run lite LHC10H_AOD160

Or submit it to the grid::
    
  $ nitty run grid LHC10H_AOD160

Once your analysis is finished on the grid, change to the output dir (`latest`) and trigger the merging::
    
  $ cd latest
  $ nitty merge online

Once all the final merging stages are reached, you can merge individual runs offline on your own computer::
    
  $ nitty merge offline


What is happening behind the scene?
===================================

When running your analysis nitty griddy create a new folder in your project folder. It then generates a `run.C` file from your options and copies it into that folder. This `run.C` can be run on independently and should be easy to read. This has the advantage that you can always just stop using `nittygriddy` and drop back to modifying the macros yourself - no vendor lockin! However, if you would like to continue using `nittygriddy`, you should not edit those macros directly since they might get overwritten and it defeats the purpose of this program in the first place.
