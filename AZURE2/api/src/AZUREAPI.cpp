#include "AZUREAPI.h"
#include "AZUREParams.h"

#include "GSLException.h"

#include "Config.h"
#include "CNuc.h"
#include "EData.h"

#include <iostream>
#include <iomanip>
#include <fstream>
#include <limits>
#include <new>

bool AZUREAPI::Initialize( ){

  configure().paramMask |= Config::USE_EXTERNAL_CAPTURE;

  std::string file;
  if( configure().paramMask & Config::CALCULATE_WITH_DATA ) file = configure().outputdir + "intEC.dat";
  else file = configure().outputdir + "intEC.extrap";

  std::ifstream in(file.c_str());
  if( !in ) configure().paramMask &= ~Config::USE_PREVIOUS_INTEGRALS;
  else configure().paramMask |= Config::USE_PREVIOUS_INTEGRALS;

  configure().integralsfile=file;

  if( compound_ != nullptr ) delete compound_;
  if( data_ != nullptr ) delete data_;

  data_ = new EData( );
  compound_ = new CNuc( );

  //configure().outStream << "Filling Compound Nucleus..." << std::endl;
  if(compound()->Fill(configure())==-1) {
    //configure().outStream << "Could not fill compound nucleus from file." << std::endl;
    return -1;
  } else if(compound()->NumPairs()==0 || compound()->NumJGroups()==0) {
    //configure().outStream << "No nuclear data exists. Calculation not possible." << std::endl; 
    return -1;
  } 
  if((configure().screenCheckMask|configure().fileCheckMask) & 
     Config::CHECK_COMPOUND_NUCLEUS) compound()->PrintNuc(configure());

  if(!(configure().paramMask & Config::CALCULATE_REACTION_RATE)) {
    //Fill the data object from the segments and data file
    //  Compound object is passed to the function for pair key verification and
    //  center of mass conversions, s-factor conversions, etc.
    //configure().outStream << "Filling Data Structures..." << std::endl;
    if(configure().paramMask & Config::CALCULATE_WITH_DATA) {
      if(data()->Fill(configure(),compound())==-1) {
	//configure().outStream << "Could not fill data object from file." << std::endl;
	return -1;
      } else if(data()->NumSegments()==0) {
	//configure().outStream << "There is no data provided." << std::endl;
	return -1;
      }
    } else {
      if(data()->MakePoints(configure(),compound())==-1) {
	//configure().outStream << "Could not fill data object from file." << std::endl;
	return -1;
      } else if(data()->NumSegments()==0) {
	//configure().outStream << "Extrapolation segments produce no data." << std::endl;
	return -1;
      }
    } 
    if((configure().fileCheckMask|configure().screenCheckMask) & Config::CHECK_DATA)
      data()->PrintData(configure());
  } else {
    if(!compound()->IsPairKey(configure().rateParams.entrancePair)||!compound()->IsPairKey(configure().rateParams.exitPair)) {
      //configure().outStream << "Reaction rate pairs do not exist in compound nucleus." << std::endl;
      return -1;
    } else {
      compound()->GetPair(compound()->GetPairNumFromKey(configure().rateParams.entrancePair))->SetEntrance();
    }
  }

  //Initialize compound nucleus object
  try {
    compound()->Initialize(configure());
  } catch (GSLException e) {
    configure().outStream << e.what() << std::endl;
    configure().outStream << std::endl
			  << "Calculation was aborted." << std::endl;
    return -1;
  }

  if(data()->Initialize(compound(),configure())==-1) return -1;

  return 0;
  
}

bool AZUREAPI::UpdateParameters( ) {

  names_.clear( );
  fixed_.clear( );
  values_.clear( );
  transform_.clear( );

  AZUREParams params;
  compound()->FillMnParams(params.GetMinuitParams());
  data()->FillMnParams(params.GetMinuitParams());

  compound()->FillCompoundFromParams(params.GetMinuitParams( ).Params( ));

  compound()->CalcShiftFunctions( configure() );
  compound()->TransformOut( configure() );

  for(int i = 0; i < params.GetMinuitParams().Params().size(); i++){
    names_.push_back( params.GetMinuitParams().Parameter(i).GetName() );
    fixed_.push_back( params.GetMinuitParams().Parameter(i).IsFixed() );
    values_.push_back( params.GetMinuitParams().Parameter(i).Value() );
  }

  transform_ = compound()->GetTransformParams( configure() );

  return true;

}

int AZUREAPI::UpdateSegments(vector_r& p) {

  calculatedSegments_.clear( );
  calculatedEnergies_.clear( );

  CNuc* localCompound = NULL;
  EData* localData = NULL;
  localCompound = compound();
  localData = data();


  AZUREParams params;
  localCompound->FillCompoundFromParamsPhysical(p);
  bool isValid = localCompound->TransformIn( configure( ) );


  if( !isValid ){
    return 0;
  }

  localCompound->FillMnParams(params.GetMinuitParams());
  localData->FillMnParams(params.GetMinuitParams());
  localCompound->FillCompoundFromParams(params.GetMinuitParams( ).Params( ));

  //Fill Compound Nucleus From Minuit Parameters
  if(configure().paramMask & Config::USE_BRUNE_FORMALISM) localCompound->CalcShiftFunctions(configure());

  int newKey  = -1;
  int prevKey = -1;
  int nSegments = 0;

  std::vector<ESegment>& segments = localData->GetSegments( );
  for( int i = 0; i < segments.size( ); ++i ){
    
    newKey = segments[i].GetSegmentKey( );
    if( prevKey == newKey ) continue;
    prevKey = newKey; ++nSegments;

    std::vector<EPoint>& data = segments[i].GetPoints();

    std::vector<double> cross, energies;;
    for( int k = 0; k < data.size( ); ++k ){

      if(!data[k].IsMapped()) data[k].Calculate(localCompound,configure());

      cross.push_back( data[k].GetFitCrossSection() );
      energies.push_back( data[k].GetCMEnergy( ) );


    }

    calculatedSegments_.push_back( cross );
    calculatedEnergies_.push_back( energies );

  }

  return calculatedSegments_.size( );

}

bool AZUREAPI::CalculateExternalCapture( ){

  configure().paramMask &= ~Config::USE_PREVIOUS_INTEGRALS;
  data()->CalculateECAmplitudes( compound( ), configure( ) );
  configure().paramMask |= Config::USE_PREVIOUS_INTEGRALS;

  return true;

}

int AZUREAPI::UpdateData( ) {

  dataEnergies_.clear( );
  dataSegments_.clear( );
  dataSegmentsErrors_.clear( );

  CNuc* localCompound = NULL;
  EData* localData = NULL;
  localCompound = compound();
  localData = data();

  int newKey  = -1;
  int prevKey = -1;
  int nSegments = 0;

  std::vector<ESegment>& segments = localData->GetSegments( );
  for( int i = 0; i < segments.size( ); ++i ){
    
    newKey = segments[i].GetSegmentKey( );
    if( prevKey == newKey ) continue;
    prevKey = newKey; ++nSegments;

    std::vector<EPoint>& data = segments[i].GetPoints();

    std::vector<double> energies, cross, crossErr;
    for( int k = 0; k < data.size( ); ++k ){

      energies.push_back( data[k].GetCMEnergy( ) );
      cross.push_back( data[k].GetCMCrossSection() );
      crossErr.push_back( data[k].GetCMCrossSectionError() );

    }

    dataEnergies_.push_back( energies );
    dataSegments_.push_back( cross );
    dataSegmentsErrors_.push_back( crossErr );

  }

  return nSegments;

}

void AZUREAPI::UpdateNorms( ) {

  norms_.clear( );
  normsErrors_.clear( );

  CNuc* localCompound = NULL;
  EData* localData = NULL;
  localCompound = compound();
  localData = data();

  int newKey  = -1;
  int prevKey = -1;
  int nSegments = 0;

  std::vector<ESegment>& segments = localData->GetSegments( );
  for( int i = 0; i < segments.size( ); ++i ){
    
    newKey = segments[i].GetSegmentKey( );
    if( prevKey == newKey ) continue;
    prevKey = newKey; ++nSegments;

    double norm = segments[i].GetNominalNorm( );
    double normErr = segments[i].GetNormError( );

    norms_.push_back( norm );
    normsErrors_.push_back( normErr );

  }

}

// Set AZURE2 to calculate data points
void AZUREAPI::SetData( ) { 
  configure().paramMask |= Config::CALCULATE_WITH_DATA; 
}

// Set AZURE2 to calculate extrapolations
void AZUREAPI::SetExtrap( ) { 
  configure().paramMask &= ~Config::CALCULATE_WITH_DATA; 
}

// Set radius to a fixed value
void AZUREAPI::SetRadius( int idx, double r ) {
  
  if( compound_ != nullptr ) delete compound_;
  if( data_ != nullptr ) delete data_;

  compound_ = new CNuc;
  data_     = new EData;

  std::pair<int,double> pair = std::make_pair( idx, r );

  compound()->Fill( configure( ), pair  );
  data()->Fill(configure(),compound());

  configure().paramMask &= ~Config::USE_PREVIOUS_INTEGRALS;
  compound( )->Initialize( configure( ) );
  data( )->Initialize( compound( ), configure( ) );
  configure().paramMask |= Config::USE_PREVIOUS_INTEGRALS;

}