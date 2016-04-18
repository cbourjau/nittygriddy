/* 
 * This is an automatically generated file. Do yourself a favour and
 * do __not__ edit it by hand. It will be overwritten eventually and
 * you will be sad. Instead file an issue over at the nittygriddy
 * gitlab page, please.
 */

#ifndef __CINT__
#include <fstream>
#include <iostream>
#include <vector>

#include "TROOT.h"
#include "TProof.h"
#include "TChain.h"
#include "TObject.h"
#include "TList.h"
#include "TString.h"

#include "AliAnalysisManager.h"
#include "AliMCEventHandler.h"
#include "AliESDInputHandler.h"
#include "AliAODInputHandler.h"
#include "AliAnalysisGrid.h"
#include "AliAnalysisAlien.h"
#include "AliMultSelectionTask.h"
#include "AddTaskC2.C"

#endif

enum {kLOCAL, kLITE, kPOD, kGRID};

void loadLibs(const TString extralibs, const Int_t runmode){
  if (runmode == kLOCAL || runmode == kGRID){
    // for running with root only
    gSystem->Load("libTree.so");
    gSystem->Load("libGeom.so");
    gSystem->Load("libVMC.so");
    gSystem->Load("libSTEERBase.so");
    gSystem->Load("libESD.so");
    gSystem->Load("libAOD.so"); 

    // load extra analysis libs
    TIter it(extralibs.Tokenize(" "));
    TObjString *lib = 0;
    while ((lib = dynamic_cast<TObjString *>(it()))){
      if (gSystem->Load(lib->String()) < 0) {
	std::cout << "Error loading " << lib->String() << std::endl;
      }
    }
  }
  else{
    TList *list = new TList();
    list->Add(new TNamed("ALIROOT_EXTRA_LIBS", extralibs.ReplaceAll(" ", ":").Data()));
    TString alicePar;
    
    if ((runmode == kLITE)){
      alicePar  = "$ALICE_ROOT/ANALYSIS/macros/AliRootProofLite.par";
    }
    
    if (runmode == kPOD){
      // A single AliRoot package for *all* AliRoot versions: new on VAF
      alicePar = "/afs/cern.ch/alice/offline/vaf/AliceVaf.par";
      list->Add(new TNamed("ALIROOT_ENABLE_ALIEN", "1"));  // important: creates token on every PROOF worker
    }
    gProof->UploadPackage(alicePar.Data());
    gProof->EnablePackage(alicePar.Data(), list);  // this "list" is the same as always
    std::cout << "enabled packages: " << std::endl;
    gProof->ShowEnabledPackages();
  }
}

TChain* makeChain() {
  TChain * chain = new TChain ("aodTree");
  TString incollection = "./input_files.dat";
  ifstream file_collect(incollection.Data());
  TString line;
  while (line.ReadLine(file_collect) ) {
    chain->Add(line.Data());
  }
  return chain;
}


void setUpIncludes(Int_t runmode) {
  // Set the include directories
  // gProof is without -I :P and gSystem has to be set for all runmodes
  gSystem->AddIncludePath("-I$ALICE_ROOT/include");
  if (runmode == kLITE){
    gProof->AddIncludePath("$ALICE_ROOT/include", kTRUE);
  }
}

void run()
{
  // load GetSetting.C macro to allow access to settings for this particular dataset
  gROOT->LoadMacro("./GetSetting.C");
  Int_t max_events = -1;
  Int_t runmode = -1;

  if (GetSetting("runmode") == "local")
    runmode = kLOCAL;
  else if (GetSetting("runmode") == "lite")
    runmode = kLITE;
  else if (GetSetting("runmode") == "grid")
    runmode = kGRID;
  else {
    std::cout << "Invalid analysis mode: " << GetSetting("runmode") << "! I have no idea whats going on..." << std::endl;
    assert(0);
  }
  // start proof if necessary
  if (runmode == kLITE) TProof::Open("lite://");
  else if (runmode == kPOD) TProof::Open("pod://");

  setUpIncludes(runmode);

  // Create  and setup the analysis manager
  AliAnalysisManager *mgr = new AliAnalysisManager();

  TString analysisName("AnalysisResults");
  mgr->SetCommonFileName(analysisName + TString(".root"));

  // Set Handlers TODO: depends on dataset type
  AliVEventHandler* aodH = new AliAODInputHandler;
  mgr->SetInputEventHandler(aodH);
  //AliMCEventHandler* handler = new AliMCEventHandler;
  //handler->SetReadTR(kTRUE);
  //mgr->SetMCtruthEventHandler(handler);

  if (runmode == kGRID) {
    gROOT->LoadMacro("./CreateAlienHandler.C");
    AliAnalysisGrid *alienHandler = CreateAlienHandler();
    if (!alienHandler) return;
    mgr->SetGridHandler(alienHandler);
  }

  // Add tasks
  gROOT->LoadMacro("$ALICE_PHYSICS/OADB/COMMON/MULTIPLICITY/macros/AddTaskMultSelection.C");
  AliMultSelectionTask * task = AddTaskMultSelection(kFALSE);
  // I think SetAlternateOADBforEstimators is depreciated (comment in .h file)
  if (GetSetting("period") == ""){
    task->SetAlternateOADBforEstimators(GetSetting("period").c_str());
  }

  gROOT->LoadMacro("./ConfigureWagon.C");
  ConfigureWagon();

  if (!mgr->InitAnalysis()) return;
  mgr->PrintStatus();

  if (runmode == kGRID) {
    std::cout << "Starting grid analysis" << std::endl;
    mgr->StartAnalysis("grid");
  }
  else if ((runmode == kLOCAL) || (runmode == kLITE)) {
      // Process with chain
    TChain *chain = makeChain();
      if (!chain) {
	std::cout << "Dataset is empty!" << std::endl;
	return;
      }
      if (runmode == kLITE)
	mgr->StartAnalysis("proof", chain, max_events);

      else if (runmode == kLOCAL) {
	// in order to be inconvinient, aliroot does interprete max_events differently for proof and local :P
	if (max_events == -1) mgr->StartAnalysis("local", chain);
	else mgr->StartAnalysis("local", chain, max_events);
      }
    }
  // else if (runmode == kPOD){
  //   // process with dataset string
  //   TString dataset = getDatasetString(incollection);
  //   // Check the dataset before running the analysis!
  //   gProof->ShowDataSet( dataset.Data() );
  //   mgr->StartAnalysis("proof", dataset, max_events, 0 /*first_event*/);
  // }
}
