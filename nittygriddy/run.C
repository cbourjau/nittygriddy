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
enum {kGRID_FULL, kGRID_OFFLINE, kGRID_TEST, kGRID_MERGE_ONLINE, kGRID_MERGE_OFFLINE};

struct settings {
  TString kPERIOD;
  TString kLOCALDATA;
  TString kGRIDWORKDIR;
  TString kGRIDDATADIR;
  TString kGRIDDATAPATTERN;
  TString kGRIDRUNLIST;
};

Int_t kGRIDMODE = kGRID_FULL;
TString kALICE_PHYSICS = "vAN-20160405-1";

settings getSettings(const char* settingName) {
  if (TString(settingName).BeginsWith("15k1a1")) {
    settings _15k1a1 = {
      /*.kPERIOD =*/ "LHC15k1a1",
      /*.kLOCALDATA =*/ "/home/christian/lhc_data/alice/sim/2015/LHC15k1a1/input_files.dat",
      /*.kGRIDWORKDIR =*/ "PbPbMC_20160207_0",
      /*.kGRIDDATADIR =*/ "/alice/sim/2015/LHC15k1a1",
      /*.kGRIDDATAPATTERN =*/ "AOD/*/AliAOD.root", // is this correct?!
      /*.kGRIDRUNLIST =*/ "244918 244975 244982 244983 245064"
    };
    return _15k1a1;
  }
  else if (TString(settingName).BeginsWith("15f4")) {
    settings _15f4 = {
      /*.kPERIOD=*/ "LHC15f",
      /*.kLOCALDATA =*/ "/home/christian/lhc_data/alice/sim/2015/LHC15f4/input_files.dat",
      /*.kGRIDWORKDIR =*/ "pp13MC_20160211_0",
      /*.kGRIDDATADIR =*/ "/alice/sim/2015/LHC15f4",
      /*.kGRIDDATAPATTERN =*/ "AOD/*/AliAOD.root",
      /*.kGRIDRUNLIST =*/ "225035 225106 225709 226062"
    };
    return _15f4;
  }
  else if (TString(settingName).BeginsWith("10h")) {
    settings _10h = {
      /*.kPERIOD=*/ "",
      /*.kLOCALDATA =*/ "/home/christian/lhc_data/alice/data/2010/LHC10h/input_files.dat",
      /*.kGRIDWORKDIR =*/ "PbPb_10h_20160405_0",
      /*.kGRIDDATADIR =*/ "/alice/data/2010/LHC10h",
      /*.kGRIDDATAPATTERN =*/ "ESDs/pass2/AOD160/*/AliAOD.root",
      /*.kGRIDRUNLIST =*/ "139510, 139507, 139505, 139503, 139465, 139438"
    };
    return _10h;
  }
  else {
    std::cout << "bad settings name given!" << std::endl;
    return settings();
  }
}

void configureWagonC2() {
  gROOT->LoadMacro("$ALICE_PHYSICS/PWGCF/Correlations/macros/c2/AddTaskC2.C");
  AliAnalysisTaskC2* task =
    reinterpret_cast< AliAnalysisTaskC2* > (gROOT->ProcessLine("AddTaskC2()"));
  task->fSettings.fDataType = AliAnalysisC2Settings::kRECON;

  task->fSettings.fPtBinEdges = std::vector< Double_t >();
  task->fSettings.fPtBinEdges.push_back(2);
  task->fSettings.fPtBinEdges.push_back(3);
  task->fSettings.fPtBinEdges.push_back(4);
  task->fSettings.fPtBinEdges.push_back(6);
  task->fSettings.fPtBinEdges.push_back(8);
}

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
  // TString incollection = "";  //// replace-token incollection
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
void loadAnalysisFiles(const TString files, TString runmode ) {
  // load files from colon (:) separated string
  // first file in string is loaded first (OBS: dependencies)
  // The function does the right thing regardless if local, lite or pod
  // Do not use ++ in the string to avoid unnecessary recompiles on nodes

  // loop over analysis files given by the user
  TIter it(files.Tokenize(" "));
  TObjString *lib = 0;
  while ((lib = dynamic_cast<TObjString *>(it()))){
    Int_t status;
    if (runmode == kLOCAL)
      status = gROOT->LoadMacro(lib->String());
    else if (runmode == kPOD || runmode == kLITE)
      status = gProof->Load(lib->String());
    if (status !=0){
	std::cout << "Error loading " << lib->String() << std::endl;
    }
  }
}

AliAnalysisGrid* CreateAlienHandler(TString sourcefiles, TString settingName) {
  // Create a generic alien grid handler. Ie, one still needs to add the analysis files to the plugin
  Bool_t isMC = false;
  AliAnalysisAlien *plugin = new AliAnalysisAlien();

  plugin->AddIncludePath("-I. -I$ROOTSYS/include -I$ALICE_ROOT/include -I$ALICE_PHYSICS/include");
  //plugin->SetAnalysisSource("AliAnalysisTaskC2.cxx");
  plugin->SetAdditionalLibs(
			    "libOADB.so libSTEERBase.so" //// replace-token dependencies
			    );
  plugin->SetOverwriteMode();
  plugin->SetExecutableCommand("aliroot -q -b");
  // Can be "full", "test", "offline", "submit" or "merge"
  // merging only works in "full" mode?!
  if (kGRID_OFFLINE == kGRIDMODE){
    plugin->SetRunMode("offline");
    // The following option is necessary to write the merge jdl's
    plugin->SetMergeViaJDL(true);
  }
  else if (kGRID_TEST == kGRIDMODE)
    plugin->SetRunMode("test");
  else if (kGRID_FULL == kGRIDMODE) {
    plugin->SetRunMode("full");
    plugin->SetMergeViaJDL(true);
  }
  else if (kGRID_MERGE_ONLINE == kGRIDMODE){
    plugin->SetRunMode("terminate");
    plugin->SetMergeViaJDL(true);
  }
  else if (kGRID_MERGE_OFFLINE == kGRIDMODE){
    plugin->SetRunMode("terminate");
    plugin->SetMergeViaJDL(false);  // turn this to false after the final merging to merge runs
  }

  plugin->SetNtestFiles(1);
  //Set versions of used packages
  plugin->SetAliPhysicsVersion(kALICE_PHYSICS);

  // Declare input data to be processed
  plugin->SetGridDataDir(getSettings(settingName).kGRIDDATADIR.Data());
  plugin->SetDataPattern(getSettings(settingName).kGRIDDATAPATTERN.Data());
  plugin->SetGridWorkingDir(getSettings(settingName).kGRIDWORKDIR);
  plugin->SetAnalysisMacro("myAnalysisMacro.C");
  plugin->SetExecutable("myAnalysisExec.sh");
  plugin->SetJDLName("myTask.jdl");
  plugin->SetDropToShell(false);  // do not open a shell

  if(isMC)
    plugin->SetRunPrefix(""); 
  else
    plugin->SetRunPrefix("000"); 

  plugin->AddRunList(getSettings(settingName).kGRIDRUNLIST);

  plugin->SetGridOutputDir("output"); // In this case will be $HOME/work/output 
  plugin->SetMaxMergeFiles(25);
  plugin->SetMergeExcludes("EventStat_temp.root"
			   "event_stat.root");

  plugin->SetOutputToRunNo();     // Use run number as output folder names
  plugin->SetTTL(15*3600);
  // Optionally set input format (default xml-single)
  plugin->SetInputFormat("xml-single");
  // Optionally modify job price (default 1)
  plugin->SetPrice(1);      
  // Optionally modify split mode (default 'se')    
  //plugin->SetSplitMaxInputFileNumber();
  plugin->SetSplitMode("se");
  return plugin;
}


void run(const TString runmode_str  = "lite",
	 Int_t max_events = 100,
	 //Int_t first_event= 0,
	 const char * aliceExtraLibs=(""
				      //"libpythia6_4_25 "
				      //"libAliPythia6"
				      )
	 )
{  
  // std::cin.ignore();  // wait to connect gdb
  Int_t runmode = -1;
  if(runmode_str.BeginsWith("local"))
    runmode = kLOCAL;
  else if(runmode_str.BeginsWith("lite"))
    runmode = kLITE;
  else if(runmode_str.BeginsWith("pod"))
    runmode = kPOD;
  else if(runmode_str.BeginsWith("grid"))
    runmode = kGRID;
  else {
    std::cout << "invalid runmode given" << std::endl;
    return;
  }

  // start proof if necessary
  if (runmode == kLITE) TProof::Open("lite://");
  else if (runmode == kPOD) TProof::Open("pod://");

  setUpIncludes(runmode);
  loadLibs(aliceExtraLibs, runmode);

  // Create  and setup the analysis manager
  AliAnalysisManager *mgr = new AliAnalysisManager();

  // Enable debug printouts
  mgr->SetDebugLevel(debug);
  

  mgr->SetCommonFileName(TString(analysisName) + TString(".root"));

  // Set Handlers
  AliVEventHandler* aodH = new AliAODInputHandler;
  mgr->SetInputEventHandler(aodH);
  //AliMCEventHandler* handler = new AliMCEventHandler;
  //handler->SetReadTR(kTRUE);
  //mgr->SetMCtruthEventHandler(handler);

  if (runmode == kGRID) {
    AliAnalysisGrid *alienHandler = CreateAlienHandler(analysisFiles, settingName);
    if (!alienHandler) return;
    mgr->SetGridHandler(alienHandler);
    loadAnalysisFiles(analysisFiles, runmode_str);
  }

  // Add tasks
  gROOT->LoadMacro("$ALICE_PHYSICS/OADB/COMMON/MULTIPLICITY/macros/AddTaskMultSelection.C");
  AliMultSelectionTask * task = AddTaskMultSelection(kFALSE);
  // I think SetAlternateOADBforEstimators is depreciated (comment in .h file)
  if (!getSettings(settingName).kPERIOD.IsNull()){
    task->SetAlternateOADBforEstimators (getSettings(settingName).kPERIOD.Data());
  }

  //TIter it(adderFiles.Tokenize(" "));
  //TObjString *adder = 0;
  // while ((adder = dynamic_cast<TObjString *>(it()))){
  //   // adder files include logic to add the task to the manager, no need to do it again here
  //   gROOT->Macro(adder->String());
  // }

  configureWagonC2();

  if (!mgr->InitAnalysis()) return;
  mgr->PrintStatus();

  if (runmode_str.BeginsWith("grid")) {
    std::cout << "Starting grid analysis" << std::endl;
    mgr->StartAnalysis("grid");
  }
  else if ((runmode == kLOCAL) || (runmode == kLITE)) {
      // Process with chain
      TChain *chain = makeChain(getSettings(settingName).kLOCALDATA);
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
  else if (runmode == kPOD){
    // process with dataset string
    TString dataset = getDatasetString(incollection);
    // Check the dataset before running the analysis!
    gProof->ShowDataSet( dataset.Data() );
    mgr->StartAnalysis("proof", dataset, max_events, 0 /*first_event*/);
  }
}
