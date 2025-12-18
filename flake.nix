{
  description = "SF Street Cleaning Home Assistant Integration (Dev Environment)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    # Core pyproject-nix ecosystem tools
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs";

    # Ensure consistent dependencies between these tools
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-build-systems.inputs.nixpkgs.follows = "nixpkgs";
    uv2nix.inputs.pyproject-nix.follows = "pyproject-nix";
    pyproject-build-systems.inputs.pyproject-nix.follows = "pyproject-nix";
  };

  outputs = { self, nixpkgs, flake-utils, uv2nix, pyproject-nix, pyproject-build-systems, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python313;

        # 1. Load Project Workspace (parses pyproject.toml, uv.lock)
        workspace = uv2nix.lib.workspace.loadWorkspace {
          workspaceRoot = ./.;
        };

        # 2. Generate Nix Overlay from uv.lock
        uvLockedOverlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };

        # 3. Custom Package Overrides
        myCustomOverrides = final: prev: {
          # lru-dict has no pyproject build-system entry and needs setuptools when built from sdist
          lru-dict = prev.lru-dict.overrideAttrs (old: {
            nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ final.setuptools ];
          });
          # mock-open declares legacy setuptools backend but misses the dependency
          mock-open = prev.mock-open.overrideAttrs (old: {
            nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ final.setuptools ];
          });
          # pyric also uses legacy setuptools backend without declaring it
          pyric = prev.pyric.overrideAttrs (old: {
            nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ final.setuptools ];
          });
        };

        # 4. Construct Final Python Package Set
        pythonSet =
          (pkgs.callPackage pyproject-nix.build.packages { inherit python; })
          .overrideScope (nixpkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            uvLockedOverlay
            myCustomOverrides
          ]);

        # Project Metadata
        projectNameInToml = "sf-street-cleaning-integration";
        thisProjectAsNixPkg = pythonSet.${projectNameInToml};

        # 5. Create Python Runtime Environment
        appPythonEnv = pythonSet.mkVirtualEnv 
          (thisProjectAsNixPkg.pname + "-env") 
          workspace.deps.default;
        
        # Dev Environment with dev dependencies
        devPythonEnv = pythonSet.mkVirtualEnv
          (thisProjectAsNixPkg.pname + "-dev-env")
          workspace.deps.all;

        # Test runner (uses dev env, includes coverage)
        testRunner = pkgs.writeShellApplication {
          name = "run-tests";
          runtimeInputs = [ devPythonEnv pkgs.coreutils ];
          text = ''
            export PYTHONDONTWRITEBYTECODE=1
            coverage run -m unittest discover tests
            coverage report
          '';
        };

      in
      {
        # Development Shell
        devShells.default = pkgs.mkShell {
          packages = [ 
            devPythonEnv 
            pkgs.uv 
            pkgs.just
            pkgs.home-assistant-cli
          ];
          shellHook = ''
            export PYTHONDONTWRITEBYTECODE=1
            echo "Home Assistant Integration Dev Shell Ready."
            echo "Python $(python --version)"
          '';
        };

        packages.testRunner = testRunner;
      }
    );
}
