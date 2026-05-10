{
  description = "Unified flake";

  inputs = {
    system-flake.url = "path:/home/kein/nixos-configuration";
    nixpkgs.follows = "system-flake/nixpkgs";
    flake-utils.follows = "system-flake/flake-utils";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        overlay = final: prev: {
          python3 = prev.python3.override {
            packageOverrides =
              pyFinal: pyPrev:
              let
                callPackage = pyFinal.callPackage;
              in
              {
                # pyalex = callPackage ./nix-wiring/pyalex.nix { };
                # crossrefapi = callPackage ./nix-wiring/crossrefapi.nix { };
                # jsonc-parser = callPackage ./nix-wiring/jsonc-parser.nix { };
                # arxiv = callPackage ./nix-wiring/arxiv.nix { };
                # scidownl = callPackage ./nix-wiring/scidownl.nix { };
              };
          };

          python3Packages = final.python3.pkgs;
        };

        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay ];
          config = {
            allowUnfree = true;
          };
        };
        lib = pkgs.lib;

        pythonClosure = pkgs.python3.withPackages (
          ps: with ps; [
            isort
            numpy
            pandas
            requests
            matplotlib
            retrying

            beautifulsoup4
            loguru
            pysocks
            sqlalchemy
            wget
            setuptools
            curl-cffi
            pytest

            # type checking
            types-requests
            types-beautifulsoup4
            mypy
            flake8
            # flake8-quotes
            flake8-bugbear
            flake8-class-newline
            # flake8-debugger
            flake8-deprecated
            # flake8-docstrings
            flake8-import-order
            # flake8-length
            black
            autopep8
            ruff
          ]
        );
      in
      {
        packages = with pkgs.python3Packages; {
          # default = ;
          pythonClosure = pythonClosure;
        };

        devShells = {
          default =
            let
              # setup for VSCode editor
              repoName = "SciDownl";
              root = "/home/kein/repos/articles/nix-wiring/${repoName}";
              vscodeDir = "${root}/.vscode";
              blackCacheDir = "${vscodeDir}/black.cache";
              workspaceFileLoc = "${vscodeDir}/${repoName}.code-workspace";
              workspaceFile = pkgs.writeText "${repoName}.code-workspace" (
                builtins.toJSON {
                  folders = [
                    {
                      path = root;
                    }
                  ];
                  settings =
                    let
                      maxLineLength = "240";
                      importStrategy = "fromEnvironment";
                      ignorePatterns = [
                        # "nix-wiring/"
                      ];
                      tools = {
                        isort = "isort";
                        autopep8 = "autopep8";
                        flake8 = "flake8";
                        black = "black-formatter";
                        mypy = "mypy-type-checker";
                      };
                      interpreterPath = "${pythonClosure}/bin/python";
                    in
                    (lib.listToAttrs (
                      lib.concatLists (
                        lib.mapAttrsToList (programName: extensionName: [
                          (lib.nameValuePair "${extensionName}.importStrategy" importStrategy)
                          (lib.nameValuePair "${extensionName}.interpreter" [ interpreterPath ])
                          (lib.nameValuePair "${extensionName}.path" [
                            interpreterPath
                            "-m"
                            programName
                          ])
                        ]) tools
                      )
                    ))
                    // {
                      "python.analysis.typeCheckingMode" = "standard";
                      # "python.formatting.provider" = "ms-python.black-formatter";
                      "[python]" = {
                        "editor.defaultFormatter" = "ms-python.black-formatter";
                      };
                      "python.analysis.exclude" = ignorePatterns;

                      "mypy-type-checker.reportingScope" = "workspace";
                      "mypy-type-checker.args" = [
                        # "--disable-error-code=import-untyped"
                      ];
                      "mypy-type-checker.ignorePatterns" = ignorePatterns;

                      "flake8.args" = [
                        "--max-line-length=${maxLineLength}"
                        "--import-order-style=appnexusStyle"
                      ];
                      "flake8.ignorePatterns" = ignorePatterns;

                      "black-formatter.args" = [
                        "--line-length=${maxLineLength}"
                      ];

                      "autopep8.args" = [
                        "--max-line-length=${maxLineLength}"
                      ];

                    };
                }
              );
            in
            pkgs.mkShell {
              buildInputs = with pkgs; [
                jq
                pyright

                # not needed yet
                # texlive.combined.scheme-full
                # pkg-config
                # meson
                # ninja
                # gfortran14

                pythonClosure
              ];

              env = {
                BETTER_CODE_VSCODE_WORKSPACE_FILE = workspaceFileLoc;
                BLACK_CACHE_DIR = blackCacheDir;
              };

              shellHook = ''
                mkdir -p ${vscodeDir}
                cat ${workspaceFile} | ${pkgs.jq}/bin/jq . > '${workspaceFileLoc}'
                ${pkgs.libnotify}/bin/notify-send 'Python is here:' '${pythonClosure}'
                echo '-----------------------'
                echo 'Python is available at:'
                echo '${pythonClosure}'
                echo '-----------------------'
                mkdir -p ${blackCacheDir}
              '';
              # export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib.outPath}/lib:$LD_LIBRARY_PATH";
            };
        };

        # apps = with pkgs.python3Packages; {
        #   mineru = {
        #     type = "app";
        #     program = "${mineru}/bin/mineru";
        #   };
        # };
      }
    );
}
