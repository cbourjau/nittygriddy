============
Nitty Griddy
============

Nitty griddy aims to make the deployment of analysis using the Aliroot framework easier and transparent. The goal is to eliminate the ungodly practice of copy-pasting together `run.C` files from all over the place. A nittygriddy project requires only minimum information, is reproducible and runs seamlessly in `local`, `proof lite` or `grid` mode. It makes it easy to select the datasets as well and suports downloading partial datasets for local offline development. Furthermore, nittygriddy allows for triggering merges once a grid analysis is done. All that being said, nittygriddy still produces straight forward `run.C` files, so you could always go back to those, if you chose to.


.. image:: https://imgs.xkcd.com/comics/standards.png


Installing nittygriddy
======================

In the future nittygriddy might be available on `pypi`, but for the moment you have to do the following steps: ::

  $ git clone https://gitlab.cern.ch/cbourjau/nittygriddy.git
  $ cd nittygriddy
  $ pip install -e .

This installs nittygriddy in `editable` mode, meaning that any changes to the files in the repository clone are imediately avaialable to the command line tool without the need for reinstalization. This means that updates can be raked in with a simple `git pull origin/master`.

Eitherway, the command `nitty` is now avialable on the command line, along with its hopefully helpful `--help`.

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
